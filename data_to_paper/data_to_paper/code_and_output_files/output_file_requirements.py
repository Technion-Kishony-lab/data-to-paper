from __future__ import annotations
import os
import pickle
from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import Path
from typing import Optional, Any, List, Tuple, Iterable, Dict, Type

from data_to_paper.env import MAX_SENSIBLE_OUTPUT_SIZE_TOKENS, NUM_DIGITS_FOR_FLOATS
from data_to_paper.servers.llm_call import count_number_of_tokens_in_message
from data_to_paper.servers.model_engine import ModelEngine
from data_to_paper.utils import dedent_triple_quote_str, format_text_with_code_blocks
from data_to_paper.utils.text_extractors import extract_to_nearest_newline
from data_to_paper.utils.text_numeric_formatting import round_floats
from data_to_paper.code_and_output_files.referencable_text import NumericReferenceableText, ReferencableTextProduct, \
    BaseReferenceableText

from data_to_paper.run_gpt_code.overrides.pvalue import OnStrPValue
from data_to_paper.run_gpt_code.run_issues import CodeProblem, RunIssue
from data_to_paper.utils.text_formatting import wrap_text_with_triple_quotes

from .file_view_params import ContentViewPurposeConverter, ViewPurpose
from .ref_numeric_values import ReferencedValue, HypertargetFormat

"""
OUTPUT FILEE REQUIREMENTS
-------------------------
There are two main types of requirements:

- Data: the file contains data that is not presentable to the LLM. Like: large data files, images, etc.
In this case we keep the file.

- Content: the file contains content that is presentable to the LLM. Like: text, tables, etc.
In this case we load and keep the content and typically delete the file.
"""

EXTS_TO_LABELS = {
    '.tex': 'latex',
    '.txt': 'output',
    '.csv': 'csv',
}


def get_block_label_from_filename(filename: str) -> str:
    """
    Return the block label for the filename.
    """
    ext = os.path.splitext(filename)[1]
    return EXTS_TO_LABELS.get(ext, 'output')


@dataclass(frozen=True)
class OutputFileRequirement:
    generic_filename: str
    minimal_count: int
    should_keep_file: bool = NotImplemented

    def is_wildcard(self):
        return '*' in self.generic_filename or '?' in self.generic_filename

    def matches(self, filename: str):
        return fnmatch(filename, self.generic_filename)

    def delete_if_needed(self, file_path: str):
        """
        Delete the file if needed.
        """
        if not self.should_keep_file:
            os.remove(file_path)

    def read_content(self, file_path: str) -> Optional[str]:
        """
        Return the content of the file.
        If data file, return None.
        """
        return None

    def get_content_and_delete_if_needed(self, file_path: str) -> str:
        """
        Return the content of the file, and delete it if needed.
        """
        content = self.read_content(file_path)
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
    content_view_purpose_converter: ContentViewPurposeConverter = field(default_factory=ContentViewPurposeConverter)

    def read_content(self, file_path: str) -> Any:
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

    def _to_html(self, content: Any) -> str:
        return format_text_with_code_blocks(content, from_md=True, is_html=True, width=None)

    def _to_str(self, content: Any, view_purpose: ViewPurpose) -> str:
        return str(content).strip()

    def _get_header_html(self, filename: str = None, num_file: int = 0, level: int = 3):
        return f'<h{level}>{filename}</h{level}>'

    def _get_header_llm(self, filename: str = None, num_file: int = 0,
                        view_purpose: ViewPurpose = ViewPurpose.PRODUCT, header_level: int = 3) -> str:
        if view_purpose.is_for_llm():
            return f'### {filename}'
        return f'"{filename}"'

    def _get_header_paper(self, filename: str = None, num_file: int = 0,
                          view_purpose: ViewPurpose = ViewPurpose.PRODUCT, header_level: int = 3) -> str:
        return f'% {filename}'

    def get_header(self, filename: str = None, num_file: int = 0,
                   view_purpose: ViewPurpose = ViewPurpose.PRODUCT,
                   header_level: int = 3) -> str:
        if view_purpose == ViewPurpose.APP_HTML:
            return self._get_header_html(filename, num_file, header_level)
        if view_purpose.is_for_llm():
            return self._get_header_llm(filename, num_file, view_purpose, header_level)
        if view_purpose.is_for_paper():
            return self._get_header_paper(filename, num_file, view_purpose, header_level)
        return f'"{filename}"'

    def get_pretty_content(self, content: Any, filename: str = None, num_file: int = 0,
                           view_purpose: ViewPurpose = ViewPurpose.PRODUCT) -> str:
        view_params = self.content_view_purpose_converter.convert_view_purpose_to_view_params(view_purpose)
        with OnStrPValue(view_params.pvalue_on_str):
            if view_purpose == ViewPurpose.APP_HTML:
                content = self._to_html(content)
            else:
                content = self._to_str(content, view_purpose)
        if view_purpose.is_for_llm():
            content = wrap_text_with_triple_quotes(content, get_block_label_from_filename(filename))
        return content

    def get_pretty_content_with_header(self, content: Any, filename: str = None, num_file: int = 0,
                                       view_purpose: ViewPurpose = ViewPurpose.PRODUCT,
                                       header_level: Optional[int] = 3) -> str:
        content = self.get_pretty_content(content, filename, num_file, view_purpose)
        if header_level:
            header = self.get_header(filename, num_file, view_purpose)
            if header:
                return header + '\n' + content
        return content


@dataclass(frozen=True)
class ReferencableContentOutputFileRequirement(BaseContentOutputFileRequirement):
    hypertarget_prefixes: Optional[Tuple[str]] = None  # List of hypertarget prefixes to assign for each file
    referenceable_text_product_cls: Type[ReferencableTextProduct] = ReferencableTextProduct
    referenceable_text_cls: Type[BaseReferenceableText] = NumericReferenceableText

    def get_pretty_content(self, content: Any, filename: str = None, num_file: int = 0,
                           view_purpose: ViewPurpose = None) -> str:
        if view_purpose == ViewPurpose.APP_HTML:
            content = self.get_pretty_content(content, filename, num_file, ViewPurpose.PRODUCT)
            return super().get_pretty_content(content, filename, num_file, view_purpose)
        else:
            content = super().get_pretty_content(content, filename, num_file, view_purpose)
        return self.get_formatted_text_and_header_references(content, filename, num_file, view_purpose)[0]

    def get_formatted_text_and_header_references(self, content: Any, filename: str = None, num_file: int = 0,
                                                 view_purpose: ViewPurpose = None) -> Tuple[str, List[ReferencedValue]]:
        referencable_text = self._get_referencable_text(content, filename, num_file, view_purpose)
        return referencable_text.get_formatted_text_and_header_references(
            hypertarget_format=self._get_hyper_target_format(view_purpose))

    def _get_referencable_text(self, content: Any, filename: str = None, num_file: int = 0,
                               view_purpose: ViewPurpose = None) -> BaseReferenceableText:
        return self.referenceable_text_cls(
            text=content,
            hypertarget_prefix=self.hypertarget_prefixes[num_file] if self.hypertarget_prefixes else None,
        )

    def _get_hyper_target_format(self, view_purpose: ViewPurpose) -> HypertargetFormat:
        return self.content_view_purpose_converter.convert_view_purpose_to_view_params(view_purpose).hypertarget_format


@dataclass(frozen=True)
class PickleContentOutputFileRequirement(ReferencableContentOutputFileRequirement):
    should_keep_file: bool = True

    def read_content(self, file_path: str) -> Any:
        """
        Return the content of the file.
        """
        with open(file_path, 'rb') as file:
            return pickle.load(file)


@dataclass(frozen=True)
class TextContentOutputFileRequirement(ReferencableContentOutputFileRequirement):
    should_keep_file: bool = False
    max_tokens: Optional[int] = MAX_SENSIBLE_OUTPUT_SIZE_TOKENS.val

    def get_issues_for_output_file_content(self, filename: str, content: str) -> List[RunIssue]:
        issues = super().get_issues_for_output_file_content(filename, content)

        if len(content.strip()) == 0:
            # The output file is empty.
            issues.append(RunIssue(
                category='Problem in output file(s)',
                item=filename,
                issue=f'The code created the output file "{filename}", but the file is just empty!',
                instructions="Please revise the code to make sure it correctly writes to the output file.",
                code_problem=CodeProblem.OutputFileContentLevelA,
            ))

        if self.max_tokens is not None \
                and count_number_of_tokens_in_message(content, max(ModelEngine)) > self.max_tokens:
            # Created output file is too large.
            issues.append(RunIssue(
                category='Problem in output file(s)',
                item=filename,
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
class NumericTextContentOutputFileRequirement(ReferencableContentOutputFileRequirement):
    target_precision: int = NUM_DIGITS_FOR_FLOATS
    source_precision: int = 10

    def _to_str(self, content: Any, view_purpose: ViewPurpose) -> str:
        content = super()._to_str(content, view_purpose)
        return round_floats(content, self.target_precision, self.source_precision)


class OutputFileRequirements(Tuple[OutputFileRequirement]):
    """
    Stores a list of requirements for the output files of an LLM code run.
    """

    def get_all_allowed_created_filenames(self) -> Tuple[str, ...]:
        return tuple(requirement.generic_filename for requirement in self)

    def _match_files_to_requirements(self, created_files: Iterable[str]) -> Dict[str, Optional[OutputFileRequirement]]:
        """
        Return a dictionary mapping each file to the requirement that it matches.
        If a file does not match any requirement, the value is None.
        """
        file_to_requirement = {}
        for created_file in created_files:
            for requirement in self:
                if requirement.matches(created_file):
                    file_to_requirement[created_file] = requirement
                    break
            else:
                file_to_requirement[created_file] = None
        return file_to_requirement

    def get_requirements_to_output_files(
            self, created_files: Iterable[str]) -> Dict[OutputFileRequirement, List[str]]:
        """
        Return a dictionary mapping each requirement to a list of output files that match it.
        """
        requirements_to_files = {requirement: [] for requirement in self}
        for created_file, requirement in self._match_files_to_requirements(created_files).items():
            if requirement is not None:
                requirements_to_files[requirement].append(created_file)
        return requirements_to_files

    def get_unmatched_files(self, created_files: Iterable[str]) -> List[str]:
        return [created_file for created_file, requirement in self._match_files_to_requirements(created_files).items()
                if requirement is None]

    def convert_to_output_file_requirements_with_content(self, created_files: Iterable[str],
                                                         run_folder) -> OutputFileRequirementsToFileToContent:
        """
        Returns an OutputFileRequirementsToFileToContent, which is a dictionary mapping each requirement to
        a dictionary mapping each output file to its content.
        """
        requirements_to_files = self.get_requirements_to_output_files(sorted(created_files))
        requirements_to_files_to_content = \
            {requirement: {
                output_file: requirement.get_content_and_delete_if_needed(
                    file_path=run_folder / output_file if run_folder else output_file)
                for output_file in files
            } for requirement, files in requirements_to_files.items()}
        return OutputFileRequirementsToFileToContent(requirements_to_files_to_content)


class OutputFileRequirementsToFileToContent(Dict[OutputFileRequirement, Dict[str, Any]]):
    """
    A dictionary mapping each requirement to a dictionary mapping each output file to its content.
    Allows to get textual content of the files.
    """

    def convert_to_output_file_requirements(self) -> OutputFileRequirements:
        return OutputFileRequirements(self.keys())

    def get_all_created_files(self) -> List[str]:
        """
        Return the names of all the files created by the run.
        """
        return [filename for filenames_to_contents in self.values() for filename in filenames_to_contents.keys()]

    def get_all_created_and_undeleted_files(self) -> List[str]:
        """
        Return the names of all the files created by the run, and which were kept, not deleted.
        """
        return [filename for requirement, files_to_contents in self.items()
                for filename in files_to_contents.keys() if requirement.should_keep_file]

    def _get_created_files_to_requirements_and_contents(self, match_filename: str = '*',
                                                        is_content: bool = None,
                                                        ) -> Dict[str, Tuple[OutputFileRequirement, Any]]:
        """
        Return the names of the files created by the run, and their requirements and content.
        Content is `None` for data files.
        is_content:
            True: return only content files
            False: return only data files
            None: return all files
        """
        return {filename: (requirement, content) for requirement, files_to_contents in self.items()
                for filename, content in files_to_contents.items() if fnmatch(filename, match_filename)
                and (is_content is None or is_content == (content is not None))}

    def get_created_content_files_to_contents(self, match_filename: str = '*') -> Dict[str, Any]:
        """
        Return the names of the files created by the run, and their content.
        """
        return {filename: content for filename, (requirement, content) in
                self._get_created_files_to_requirements_and_contents(match_filename, is_content=True).items()}

    def get_created_content_files(self, match_filename: str = '*') -> List[str]:
        """
        Return the names of the files created by the run, for which we collected the content.
        """
        return list(self.get_created_content_files_to_contents(match_filename).keys())

    def get_created_data_files(self, match_filename: str = '*') -> List[str]:
        """
        Return the names of the files created by the run, and which were kept, not deleted.
        """
        return list(self._get_created_files_to_requirements_and_contents(match_filename, is_content=False).keys())

    def delete_all_created_files(self, run_folder: Optional[Path] = None):
        """
        Delete all the files that were created by the run, and which were kept, not deleted.
        """
        for filename in self.get_all_created_files():
            filepath = run_folder / filename if run_folder else filename
            if os.path.exists(filepath):
                os.remove(filepath)

    def get_created_content_files_to_pretty_contents(self, view_purpose: ViewPurpose,
                                                     match_filename: str = '*',
                                                     header_level: Optional[int] = 3) -> Dict[str, str]:
        """
        Return the names of the files created by the run, and their content formatted for display.
        """
        files_to_pretty_contents = {}
        for requirement, files_to_contents in self.items():
            for num_file, (filename, content) in enumerate(files_to_contents.items()):
                if isinstance(requirement, BaseContentOutputFileRequirement) and fnmatch(filename, match_filename):
                    pretty_content = requirement.get_pretty_content_with_header(
                        content, filename, num_file, view_purpose, header_level=header_level)
                    files_to_pretty_contents[filename] = pretty_content

        return files_to_pretty_contents

    def get_created_content_files_and_contents_as_single_str(self, view_purpose: ViewPurpose,
                                                             match_filename: str = '*',
                                                             header_level: Optional[int] = 3) -> str:
        files_to_contents = self.get_created_content_files_to_pretty_contents(
            view_purpose=view_purpose, match_filename=match_filename, header_level=header_level)
        return '\n\n'.join(files_to_contents.values())
