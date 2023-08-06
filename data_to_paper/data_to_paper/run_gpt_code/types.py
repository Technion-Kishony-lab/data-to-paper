from dataclasses import dataclass, field

from fnmatch import fnmatch
from typing import Optional, List, Dict, Collection

from data_to_paper.base_products import DataFileDescriptions
from data_to_paper.env import MAX_SENSIBLE_OUTPUT_SIZE_TOKENS
from data_to_paper.latex.clean_latex import wrap_with_lstlisting, replace_special_latex_chars
from data_to_paper.utils.types import IndexOrderedEnum

from .overrides.dataframes.dataframe_operations import DataframeOperations
from .overrides.utils import round_floats


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


def get_single_content_file_from_requirements(requirements: Collection[OutputFileRequirement]) -> Optional[str]:
    content_file_requirements = [
        req for req in requirements
        if isinstance(req, ContentOutputFileRequirement) and not req.is_wildcard() and req.minimal_count == 1]
    if len(content_file_requirements) != 1:
        return None
    requirement = next(iter(content_file_requirements))
    return requirement.filename


@dataclass
class CodeAndOutput:
    name: str = None
    code: str = None
    requirements_to_output_files_to_contents: Dict[OutputFileRequirement, Dict[str, str]] = field(default_factory=dict)
    code_name: str = None
    code_explanation: Optional[str] = None
    dataframe_operations: Optional[DataframeOperations] = None
    description_of_created_files: DataFileDescriptions = None

    def get_single_output_filename(self) -> Optional[str]:
        return get_single_content_file_from_requirements(self.requirements_to_output_files_to_contents.keys())

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
