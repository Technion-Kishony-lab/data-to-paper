from dataclasses import dataclass, field
from fnmatch import fnmatch
from typing import Optional, List, Dict, Collection

from data_to_paper.base_products import DataFileDescriptions
from data_to_paper.env import MAX_SENSIBLE_OUTPUT_SIZE_TOKENS
from data_to_paper.latex.clean_latex import wrap_with_lstlisting

from .overrides.dataframes.dataframe_operations import DataframeOperations
from .overrides.utils import round_floats


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
        output = self.get_single_output(is_clean=True)
        if output:
            s += '\n\n' + "\\subsection{Code Output}"
            s += '\n\n' + wrap_with_lstlisting(output)
        return s
