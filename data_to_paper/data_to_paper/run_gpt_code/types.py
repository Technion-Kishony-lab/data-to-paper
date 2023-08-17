from __future__ import annotations

from dataclasses import dataclass, field

from fnmatch import fnmatch
from typing import Optional, List, Dict, Collection, Any, TYPE_CHECKING, Iterable, Tuple

from data_to_paper.base_products import DataFileDescriptions
from data_to_paper.env import MAX_SENSIBLE_OUTPUT_SIZE_TOKENS
from data_to_paper.latex.clean_latex import wrap_with_lstlisting, replace_special_latex_chars
from data_to_paper.utils.types import IndexOrderedEnum, ListBasedSet

from .overrides.utils import round_floats

if TYPE_CHECKING:
    from .overrides.dataframes.dataframe_operations import DataframeOperations

MODULE_NAME = 'script_to_run'
module_filename = MODULE_NAME + ".py"


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


@dataclass(frozen=True)
class RunIssue:
    code_problem: CodeProblem
    category: str = ''
    item: str = ''
    issue: str = ''
    instructions: str = ''
    comment: str = None
    end_with: Optional[str] = None
    requesting_small_change: bool = False
    forgive_after: int = None  # Forgive after this many times,  None means never forgive


@dataclass(frozen=True)
class RunUtilsError(Exception):
    issue: RunIssue


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
            for category in categories:
                if category:
                    s += f'# {category}\n'
                issues_in_category = [issue for issue in issues if issue.category == category]
                unique_instructions = set(issue.instructions for issue in issues_in_category)
                for issue in issues_in_category:
                    if issue.item:
                        s += f'* {issue.item}:\n'
                    s += f'{issue.issue}\n'
                    if len(unique_instructions) > 1 and issue.instructions is not None:
                        s += f'{issue.instructions}\n'
                    s += '\n'
                    if issue.comment:
                        comments.add(issue.comment)
                if len(unique_instructions) == 1:
                    shared_instructions = unique_instructions.pop()
                    if shared_instructions:
                        s += f'{shared_instructions}\n'
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

    def is_wildcard(self):
        return '*' in self.filename or '?' in self.filename

    def matches(self, filename: str):
        return fnmatch(filename, self.filename)

    @property
    def should_keep_content(self) -> bool:
        return NotImplemented


@dataclass(frozen=True)
class DataOutputFileRequirement(OutputFileRequirement):
    minimal_count: int = 0

    @property
    def should_keep_content(self) -> bool:
        return False


@dataclass(frozen=True)
class ContentOutputFileRequirement(OutputFileRequirement):
    minimal_count: int = 1
    max_tokens: int = MAX_SENSIBLE_OUTPUT_SIZE_TOKENS.val

    @property
    def should_keep_content(self) -> bool:
        return True

    def clean_content(self, content: str) -> str:
        return content


@dataclass(frozen=True)
class NumericContentOutputFileRequirement(ContentOutputFileRequirement):
    target_precision: int = 4
    source_precision: int = 10

    def clean_content(self, content: str) -> str:
        return round_floats(content, self.target_precision, self.source_precision)


class OutputFileRequirements(Tuple[OutputFileRequirement]):

    def get_all_allowed_created_filenames(self) -> Tuple[str]:
        return tuple(requirement.filename for requirement in self)

    def get_keep_content_allowed_created_filenames(self) -> Tuple[str]:
        return tuple(requirement.filename for requirement in self if requirement.should_keep_content)

    def get_single_content_file(self) -> Optional[str]:
        content_file_requirements = [
            req for req in self
            if isinstance(req, ContentOutputFileRequirement) and not req.is_wildcard() and req.minimal_count == 1]
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


@dataclass
class CodeAndOutput:
    name: str = None
    code: str = None
    result: Any = None
    requirements_to_output_files_to_contents: Dict[OutputFileRequirement, Dict[str, str]] = field(default_factory=dict)
    code_name: str = None
    code_explanation: Optional[str] = None
    dataframe_operations: Optional[DataframeOperations] = None
    description_of_created_files: DataFileDescriptions = None

    def get_single_output_filename(self) -> Optional[str]:
        return OutputFileRequirements(self.requirements_to_output_files_to_contents.keys()).get_single_content_file()

    def get_single_output(self, is_clean: bool = True) -> Optional[str]:
        """
        Return the output of the run, if it is a single content file.
        """
        single_content_filename = self.get_single_output_filename()
        if single_content_filename is None:
            return None
        return self.get_created_content_files_to_contents(is_clean)[single_content_filename]

    def get_created_content_files_to_contents(self, is_clean: bool = True) -> Dict[str, str]:
        """
        Return the names of the files created by the run, and their content.
        """
        return {filename: requirement.clean_content(content) if is_clean else content
                for requirement, files_to_contents in self.requirements_to_output_files_to_contents.items()
                for filename, content in files_to_contents.items()
                if isinstance(requirement, ContentOutputFileRequirement)}

    def get_created_data_files(self) -> List[str]:
        """
        Return the names of the files created by the run, and whose content is None.
        """
        return [filename for files_to_contents in self.requirements_to_output_files_to_contents.values()
                for filename, content in files_to_contents.items() if content is None]

    def to_latex(self):
        s = f"\\section{{{self.name}}} \\subsection{{Code}}" \
            f"The {self.name} was carried out using the following custom code:"
        s += '\n\n'
        s += '\\begin{minted}[linenos, breaklines]{python}\n' + self.code + '\n\\end{minted}\n\n'
        if self.code_explanation:
            s += "\\subsection{Code Description}"
            s += '\n\n' + self.code_explanation
        outputs = self.get_created_content_files_to_contents()
        if outputs:
            s += '\n\n' + "\\subsection{Code Output}"
            for filename, output in outputs.items():
                s += f'\n\n\\subsubsection*{{{replace_special_latex_chars(filename)}}}'
                s += '\n\n' + wrap_with_lstlisting(output)
        return s
