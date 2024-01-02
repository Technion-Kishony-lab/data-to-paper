from __future__ import annotations

import os
import pickle
from dataclasses import dataclass, field

from fnmatch import fnmatch
from pathlib import Path
from typing import Optional, List, Dict, Any, TYPE_CHECKING, Iterable, Tuple

from data_to_paper.base_products import DataFileDescriptions
from data_to_paper.env import MAX_SENSIBLE_OUTPUT_SIZE_TOKENS
from data_to_paper.latex.clean_latex import wrap_with_lstlisting, replace_special_latex_chars
from data_to_paper.utils.types import IndexOrderedEnum, ListBasedSet
from data_to_paper.servers.chatgpt import count_number_of_tokens_in_message
from data_to_paper.servers.openai_models import ModelEngine
from data_to_paper.utils import dedent_triple_quote_str, word_count
from data_to_paper.utils.text_extractors import extract_to_nearest_newline
from data_to_paper.utils.text_numeric_formatting import round_floats

from .exceptions import FailedRunningCode

if TYPE_CHECKING:
    from .overrides.dataframes.dataframe_operations import DataframeOperations

MODULE_NAME = 'script_to_run'
module_filename = MODULE_NAME + ".py"

EXTS_TO_LABELS = {
    '.tex': 'latex',
    '.txt': 'output',
    '.csv': 'csv',
}


MAX_WORDS_BEFORE_TERMINATING_ISSUE_LIST = 150


class CodeProblem(IndexOrderedEnum):
    """
    Code problems are sorted by severity, in the sense of progressively closer to a final fully working code.
    """
    NoCode = 'No code'
    IncompleteBlock = 'Incomplete block'
    NotSingleBlock = 'Not single block'
    StaticCheck = 'Static check'
    TimeoutError = 'Timeout error'
    RuntimeError = 'Runtime error'
    SyntaxError = 'Syntax error'
    MissingOutputFiles = 'Missing output files'
    NonBreakingRuntimeIssue = 'Non-breaking runtime issue'
    OutputFileContentLevelA = 'Output file content level A (specific)'
    OutputFileContentLevelB = 'Output file content level B (less specific)'
    OutputFileContentLevelC = 'Output file content level C (general)'
    OutputFileDesignLevelA = 'Output file design level A (specific)'
    OutputFileDesignLevelB = 'Output file design level B (general)'
    AllOK = 'All OK'

    def is_incomplete(self) -> bool:
        return self <= CodeProblem.IncompleteBlock

    def is_not_single_block(self) -> bool:
        return self == CodeProblem.NotSingleBlock

    def is_static_check(self) -> bool:
        return self == CodeProblem.StaticCheck

    def is_run_failed(self) -> bool:
        return CodeProblem.TimeoutError <= self <= CodeProblem.SyntaxError

    def is_missing_output_files(self) -> bool:
        return self == CodeProblem.MissingOutputFiles

    def is_run_completed_and_files_created(self) -> bool:
        return self >= CodeProblem.NonBreakingRuntimeIssue

    def get_stage(self) -> int:
        if self.is_incomplete():
            return 0
        elif self.is_not_single_block():
            return 1
        elif self.is_static_check():
            return 2
        elif self.is_run_failed():
            return 3
        elif self.is_missing_output_files():
            return 4
        elif self.is_run_completed_and_files_created():
            return 5
        else:
            raise NotImplementedError(f'Unknown problem stage for {self}')


@dataclass
class RunIssue(FailedRunningCode):
    code_problem: CodeProblem = None
    category: str = ''
    item: str = ''
    issue: str = ''
    instructions: str = ''
    comment: str = None
    end_with: Optional[str] = None
    requesting_small_change: bool = False
    forgive_after: int = None  # Forgive after this many times,  None means never forgive

    @classmethod
    def from_current_tb(cls, code_problem: CodeProblem, category: str = '', item: str = '',
                        issue: str = '', instructions: str = '', comment: str = None, end_with: Optional[str] = None,
                        requesting_small_change: bool = False, forgive_after: int = None):
        return super().from_current_tb(code_problem=code_problem, category=category, item=item,
                                       issue=issue, instructions=instructions, comment=comment, end_with=end_with,
                                       requesting_small_change=requesting_small_change, forgive_after=forgive_after)

    def __str__(self):
        return f"{self.code_problem.value}:\n{self.issue}\n{self.instructions}\n"


class RunIssues(List[RunIssue]):

    def append_if_does_not_exist(self, issue: RunIssue):
        if issue not in self:
            self.append(issue)

    def get_message_and_comment(self, most_severe_only: bool = True, end_with: str = '') -> Tuple[str, str]:
        """
        We compose all the issues into a single message, and a single comment.
        """
        issues = self._get_issues(most_severe_only)
        comments = ListBasedSet()

        s = ''
        if len(issues) > 1:
            s += 'There are some issues that need to be corrected:\n\n'

        code_problems = sorted(set(issue.code_problem for issue in issues))
        for code_problem in code_problems:
            categories = sorted(set(issue.category for issue in issues if issue.code_problem == code_problem))
            notes = []
            for category in categories:
                note = ''
                if category:
                    note += f'# {category}\n'
                issues_in_category = [issue for issue in issues if issue.category == category]
                unique_instructions = set(issue.instructions for issue in issues_in_category)
                shared_instructions = unique_instructions.pop() if len(unique_instructions) == 1 else None
                shared_instructions_word_count = word_count(shared_instructions) if shared_instructions else 0
                for issue in issues_in_category:
                    if issue.item:
                        note += f'* {issue.item}:\n'
                    if issue.linenos_and_lines:
                        note += 'On line:\n'
                        note += '\n'.join(f'{lineno}: {line}' for lineno, line in issue.linenos_and_lines)
                        note += '\n'
                    note += f'{issue.issue}\n'
                    if shared_instructions is None and issue.instructions is not None:
                        note += f'{issue.instructions}\n'
                    note += '\n'
                    if issue.comment:
                        comments.add(issue.comment)
                    if word_count(note) + shared_instructions_word_count > MAX_WORDS_BEFORE_TERMINATING_ISSUE_LIST:
                        break
                if shared_instructions is not None:
                    note += f'{shared_instructions}\n'
                notes.append(note)
            s += '\n\n'.join(notes)
        comment = '; '.join(comments)

        # Add the end_with message at the end:
        unique_end_with = set(issue.end_with for issue in issues)
        assert len(unique_end_with) == 1
        shared_end_with = unique_end_with.pop()
        if shared_end_with is not None:
            end_with = shared_end_with
        if end_with:
            s += f'\n{end_with}'
        return s, comment

    def get_most_severe_problem(self):
        return min(issue.code_problem for issue in self)

    def _get_issues(self, most_severe_only: bool = True) -> List[RunIssue]:
        if most_severe_only:
            return [issue for issue in self if issue.code_problem == self.get_most_severe_problem()]
        else:
            return list(self)

    def do_all_issues_request_small_change(self, highest_priority: bool = True) -> bool:
        return all(issue.requesting_small_change for issue in self._get_issues(highest_priority))


@dataclass(frozen=True)
class OutputFileRequirement:
    filename: str
    minimal_count: int
    should_keep_file: bool = NotImplemented

    def is_wildcard(self):
        return '*' in self.filename or '?' in self.filename

    def matches(self, filename: str):
        return fnmatch(filename, self.filename)

    def delete_if_needed(self, file_path: str):
        """
        Delete the file if needed.
        """
        if not self.should_keep_file:
            os.remove(file_path)

    def get_content(self, file_path: str) -> Optional[str]:
        """
        Return the content of the file.
        If data file, return None.
        """
        return None

    def get_content_and_delete_if_needed(self, file_path: str) -> str:
        """
        Return the content of the file, and delete it if needed.
        """
        content = self.get_content(file_path)
        self.delete_if_needed(file_path)
        return content


@dataclass(frozen=True)
class DataOutputFileRequirement(OutputFileRequirement):
    minimal_count: int = 0
    should_keep_file: bool = True


@dataclass(frozen=True)
class BaseContentOutputFileRequirement(OutputFileRequirement):
    should_keep_file: bool = NotImplemented
    minimal_count: int = 1

    def get_content(self, file_path: str) -> str:
        """
        Return the content of the file.
        """
        with open(file_path, 'r') as file:
            return file.read()

    def get_issues_for_output_file_content(self, filename: str, content: Any) -> List[RunIssue]:
        """
        Check the output and return a list of issues.
        """
        return []

    def get_pretty_content(self, content: Any) -> str:
        return str(content)


@dataclass(frozen=True)
class PickleContentOutputFileRequirement(BaseContentOutputFileRequirement):
    should_keep_file: bool = True

    def get_content(self, file_path: str) -> Any:
        """
        Return the content of the file.
        """
        with open(file_path, 'rb') as file:
            return pickle.load(file)


@dataclass(frozen=True)
class TextContentOutputFileRequirement(BaseContentOutputFileRequirement):
    should_keep_file: bool = False
    max_tokens: Optional[int] = MAX_SENSIBLE_OUTPUT_SIZE_TOKENS.val

    def get_issues_for_output_file_content(self, filename: str, content: str) -> List[RunIssue]:
        issues = super().get_issues_for_output_file_content(filename, content)

        if len(content.strip()) == 0:
            # The output file is empty.
            issues.append(RunIssue(
                item=filename,
                issue=f'The code created the output file "{filename}", but the file is just empty!',
                instructions="Please revise the code to make sure it correctly writes to the output file.",
                code_problem=CodeProblem.OutputFileContentLevelA,
            ))

        if self.max_tokens is not None \
                and count_number_of_tokens_in_message(content, max(ModelEngine)) > self.max_tokens:
            # Created output file is too large.
            issues.append(RunIssue(
                issue=dedent_triple_quote_str("""
                    The code created the output file "{}", but the file is too long!

                    Here, for context, is the beginning of the output:
                    ```output
                    {}
                    ```
                    """).format(filename, extract_to_nearest_newline(content, self.max_tokens)),
                instructions="Only sensible-length output should be written to the file.",
                code_problem=CodeProblem.OutputFileContentLevelC,
            ))

        return issues


@dataclass(frozen=True)
class NumericTextContentOutputFileRequirement(BaseContentOutputFileRequirement):
    target_precision: int = 4
    source_precision: int = 10

    def get_pretty_content(self, content: str) -> str:
        content = super().get_pretty_content(content)
        return round_floats(content, self.target_precision, self.source_precision)


class OutputFileRequirements(Tuple[OutputFileRequirement]):

    def get_all_allowed_created_filenames(self) -> Tuple[str]:
        return tuple(requirement.filename for requirement in self)

    def get_single_content_file(self) -> Optional[str]:
        content_file_requirements = [
            req for req in self
            if isinstance(req, BaseContentOutputFileRequirement) and not req.is_wildcard() and req.minimal_count == 1]
        if len(content_file_requirements) != 1:
            return None
        return content_file_requirements[0].filename

    def _get_requirements_to_output_files_and_unmatched_files(
            self, created_files: Iterable[str]) -> Tuple[Dict[OutputFileRequirement, List[str]], List[str]]:
        """
        Return:
            - a dictionary mapping each requirement to a dictionary mapping each output file to its content.
            - a list of files that were not matched to any requirement.
        """
        requirements_to_output_files = {requirement: [] for requirement in self}
        unmatched_files = []
        for created_file in created_files:
            for requirement in self:
                if requirement.matches(created_file):
                    requirements_to_output_files[requirement].append(created_file)
                    break
            else:
                unmatched_files.append(created_file)
        return requirements_to_output_files, unmatched_files

    def get_requirements_to_output_files(
            self, created_files: Iterable[str]) -> Dict[OutputFileRequirement, List[str]]:
        return self._get_requirements_to_output_files_and_unmatched_files(created_files)[0]

    def get_unmatched_files(self, created_files: Iterable[str]) -> List[str]:
        return self._get_requirements_to_output_files_and_unmatched_files(created_files)[1]

    def convert_to_output_file_requirements_with_content(self, created_files: Iterable[str],
                                                         run_folder) -> OutputFileRequirementsWithContent:
        """
        Returns an OutputFileRequirementsWithContent, which is a dictionary mapping each requirement to
        a dictionary mapping each output file to its content.
        """
        requirements_to_files = self.get_requirements_to_output_files(sorted(created_files))
        requirements_to_files_to_content = \
            {requirement: {
                output_file: requirement.get_content_and_delete_if_needed(
                    file_path=run_folder / output_file if run_folder else output_file)
                for output_file in files
            } for requirement, files in requirements_to_files.items()}
        return OutputFileRequirementsWithContent(requirements_to_files_to_content)


class OutputFileRequirementsWithContent(Dict[OutputFileRequirement, Dict[str, Any]]):
    """
    Should behave like a dictionary mapping each requirement to a dictionary mapping each output file to its content.
    """

    def convert_to_output_file_requirements(self) -> OutputFileRequirements:
        return OutputFileRequirements(self.keys())

    def get_single_content_file(self) -> Optional[str]:
        return self.convert_to_output_file_requirements().get_single_content_file()

    def get_all_created_files(self) -> List[str]:
        """
        Return the names of all the files created by the run.
        """
        return [filename for filenames_to_contents in self.values() for filename in filenames_to_contents.keys()]

    def get_created_content_files(self, match_filename: str = '*') -> List[str]:
        """
        Return the names of the files created by the run, for which we collected the content.
        """
        return [filename for requirement, files_to_contents in self.items()
                for filename in files_to_contents.keys()
                if isinstance(requirement, BaseContentOutputFileRequirement) and fnmatch(filename, match_filename)]

    def get_created_content_files_to_contents(self, is_clean: bool = True, match_filename: str = '*') -> Dict[str, str]:
        """
        Return the names of the files created by the run, and their content.
        """
        return {filename: requirement.get_pretty_content(content) if is_clean else content
                for requirement, files_to_contents in self.items()
                for filename, content in files_to_contents.items()
                if isinstance(requirement, BaseContentOutputFileRequirement) and fnmatch(filename, match_filename)}

    def get_created_content_files_description(self, match_filename: str = '*'):
        files_to_contents = self.get_created_content_files_to_contents(is_clean=True, match_filename=match_filename)
        s = ''
        for filename, content in files_to_contents.items():
            label = EXTS_TO_LABELS.get(Path(filename).suffix, 'output')
            s += f'"{filename}":\n```{label}\n{content}\n```\n\n'
        return s

    def get_single_output(self, is_clean: bool = True) -> Optional[str]:
        """
        Return the output of the run, if it is a single content file.
        """
        single_content_filename = self.get_single_content_file()
        if single_content_filename is None:
            return None
        return self.get_created_content_files_to_contents(is_clean)[single_content_filename]

    def get_created_data_files(self, match_filename: str = '*') -> List[str]:
        """
        Return the names of the files created by the run, and which were kept, not deleted.
        """
        return [filename for requirement, files_to_contents in self.items()
                for filename in files_to_contents.keys() if
                requirement.should_keep_file and fnmatch(filename, match_filename)]

    def delete_all_created_files(self, run_folder: Optional[Path] = None):
        """
        Delete all the files that were created by the run, and which were kept, not deleted.
        """
        for filename in self.get_created_data_files():
            os.remove(run_folder / filename if run_folder else filename)


@dataclass
class CodeAndOutput:
    name: str = None
    code: str = None
    result: Any = None
    created_files: \
        OutputFileRequirementsWithContent = field(default_factory=OutputFileRequirementsWithContent)
    code_name: str = None
    code_explanation: Optional[str] = None
    provided_code: Optional[str] = None
    dataframe_operations: Optional[DataframeOperations] = None
    description_of_created_files: DataFileDescriptions = None

    def to_latex(self):
        s = f"\\section{{{self.name}}}\n"
        if self.code:
            s += "\\subsection{{Code}}\n"
            s += f"The {self.name} was carried out using the following custom code:\n"
            s += '\n\\begin{minted}[linenos, breaklines]{python}\n' + self.code + '\n\\end{minted}\n\n'
        if self.provided_code:
            s += f"\\subsection{{Provided Code}}\n"
            s += f"The code above is using the following provided functions:\n"
            s += '\n\\begin{minted}[linenos, breaklines]{python}\n' + self.provided_code + '\n\\end{minted}\n\n'
        if self.code_explanation:
            s += "\\subsection{Code Description}\n"
            s += '\n' + self.code_explanation
        outputs = self.created_files.get_created_content_files_to_contents()
        if outputs:
            s += '\n\n' + "\\subsection{Code Output}"
            for filename, output in outputs.items():
                s += f'\n\n\\subsubsection*{{{replace_special_latex_chars(filename)}}}'
                s += '\n\n' + wrap_with_lstlisting(output)
        return s
