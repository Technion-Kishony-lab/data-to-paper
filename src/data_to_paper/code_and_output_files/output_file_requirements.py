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
from data_to_paper.text import dedent_triple_quote_str, wrap_as_block
from data_to_paper.text.highlighted_text import format_text_with_code_blocks
from data_to_paper.text.text_extractors import extract_to_nearest_newline
from data_to_paper.text.text_numeric_formatting import round_floats
from data_to_paper.code_and_output_files.referencable_text import NumericReferenceableText, \
    BaseReferenceableText, convert_str_to_latex_label

from data_to_paper.run_gpt_code.overrides.pvalue import OnStrPValue, OnStr
from data_to_paper.run_gpt_code.run_issues import CodeProblem, RunIssue

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


@dataclass(frozen=True)
class OutputFileRequirement:
    generic_filename: str
    minimal_count: int
    should_keep_file: bool = NotImplemented
    should_make_available_for_next_steps: bool = True

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

    """Linking"""

    def get_code_line_str_for_file(self, filename: str, content: Any) -> Optional[str]:
        """
        Return a string which can be found in the line where we should go to when we want to see the code
        that created the file.
        """
        return filename

    def get_code_line_label_for_file(self, filename: str, content: Optional[Any] = None) -> Optional[str]:
        """
        Return a label to add to the code at the line where we should go to when we want to see the code
        """
        return convert_str_to_latex_label(filename, prefix='code')

    def get_hyperlink_label_for_file_header(self, filename: str, content: Any) -> Optional[str]:
        """
        Return a hypertarget label to go to when we click the file header.
        None to not create a hyperlink.
        """
        return self.get_code_line_label_for_file(filename, content)


@dataclass(frozen=True)
class DataOutputFileRequirement(OutputFileRequirement):
    minimal_count: int = 0
    should_keep_file: bool = True


@dataclass(frozen=True)
class BaseContentOutputFileRequirement(OutputFileRequirement):
    should_keep_file: bool = NotImplemented
    minimal_count: int = 1
    content_view_purpose_converter: ContentViewPurposeConverter = field(default_factory=ContentViewPurposeConverter)
    VIEW_PURPOSE_TO_PVALUE_ON_STR = {
        ViewPurpose.PRODUCT: OnStr.SMALLER_THAN,
        ViewPurpose.HYPERTARGET_PRODUCT: OnStr.SMALLER_THAN,
        ViewPurpose.APP_HTML: OnStr.WITH_ZERO,
        ViewPurpose.CODE_REVIEW: OnStr.WITH_EPSILON,
        ViewPurpose.FINAL_APPENDIX: OnStr.WITH_ZERO,
        ViewPurpose.FINAL_INLINE: OnStr.LATEX_SMALLER_THAN,
    }

    """READ AND CHECK FILE"""

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

    """VIEW FILE"""

    def _convert_view_purpose_to_pvalue_on_str(self, view_purpose: ViewPurpose) -> OnStr:
        return self.VIEW_PURPOSE_TO_PVALUE_ON_STR[view_purpose]

    def _to_str(self, content: Any, filename: str = None, num_file: int = 0, view_purpose: ViewPurpose = None) -> str:
        pvalue_on_str = self._convert_view_purpose_to_pvalue_on_str(view_purpose)
        with OnStrPValue(pvalue_on_str):
            return str(content).strip()

    def _get_block_label(self, filename: str, num_file: int, view_purpose: ViewPurpose) -> str:
        """
        Return the block label for the filename.
        """
        ext = os.path.splitext(filename)[1]
        return EXTS_TO_LABELS.get(ext, 'output')

    def get_header(self, filename: str = None, num_file: int = 0,
                   view_purpose: ViewPurpose = ViewPurpose.PRODUCT,
                   header_level: int = 3) -> str:
        return self._get_pretty_content_and_header(None, filename, num_file, view_purpose, header_level)[1]

    def get_pretty_content(self, content: Any, filename: str = None, num_file: int = 0,
                           view_purpose: ViewPurpose = ViewPurpose.PRODUCT) -> str:
        return self._get_pretty_content_and_header(content, filename, num_file, view_purpose)[0]

    def get_pretty_content_with_header(self, content: Any, filename: str = None, num_file: int = 0,
                                       view_purpose: ViewPurpose = ViewPurpose.PRODUCT,
                                       header_level: Optional[int] = 3) -> str:
        content, header = self._get_pretty_content_and_header(content, filename, num_file, view_purpose, header_level)
        if header_level:
            newline = '<br>\n' if view_purpose.is_for_html() else '\n'
            if header:
                return header + newline + content
        return content

    def _get_pretty_content_and_header(self, content: Any, filename: str = None, num_file: int = 0,
                                       view_purpose: ViewPurpose = ViewPurpose.PRODUCT,
                                       header_level: Optional[int] = 3) -> Tuple[str, str]:
        purpose_to_func = {
            ViewPurpose.APP_HTML: self._get_content_and_header_for_app_html,
            ViewPurpose.PRODUCT: self._get_content_and_header_for_product,
            ViewPurpose.HYPERTARGET_PRODUCT: self._get_content_and_header_for_product,
            ViewPurpose.CODE_REVIEW: self._get_content_and_header_for_code_review,
            ViewPurpose.FINAL_APPENDIX: self._get_content_and_header_for_final_appendix,
            ViewPurpose.FINAL_INLINE: self._get_content_and_header_for_final_inline,
        }
        func = purpose_to_func[view_purpose]
        return func(content, filename, num_file, header_level, view_purpose)

    """Override these methods in subclasses to customize the output file content."""

    def _get_content_and_header_for_app_html(
            self, content: Any, filename: str = None, num_file: int = 0, level: int = 3,
            view_purpose: ViewPurpose = ViewPurpose.APP_HTML):
        content = self._to_str(content, filename, num_file, view_purpose)
        content = format_text_with_code_blocks(content, from_md=True, is_html=True, width=None)
        return content, f'<h{level}>{filename}</h{level}>'

    def _get_content_and_header_for_product(
            self, content: Any, filename: str = None, num_file: int = 0, level: int = 3,
            view_purpose: ViewPurpose = ViewPurpose.PRODUCT):
        content = self._to_str(content, filename, num_file, view_purpose)
        content = wrap_as_block(content, self._get_block_label(filename, num_file, view_purpose))
        return content, '#' * level + f' {filename}'

    def _get_content_and_header_for_code_review(
            self, content: Any, filename: str = None, num_file: int = 0, level: int = 3,
            view_purpose: ViewPurpose = ViewPurpose.CODE_REVIEW):
        return self._get_content_and_header_for_product(content, filename, num_file, level, view_purpose)

    def _get_content_and_header_for_final_appendix(
            self, content: Any, filename: str = None, num_file: int = 0, level: int = 3,
            view_purpose: ViewPurpose = ViewPurpose.FINAL_APPENDIX):
        return self._to_str(content, filename, num_file, view_purpose), f'% {filename}'

    def _get_content_and_header_for_final_inline(
            self, content: Any, filename: str = None, num_file: int = 0, level: int = 3,
            view_purpose: ViewPurpose = ViewPurpose.FINAL_INLINE):
        return self._to_str(content, filename, num_file, view_purpose), f'% {filename}'


@dataclass(frozen=True)
class ReferencableContentOutputFileRequirement(BaseContentOutputFileRequirement):
    hypertarget_prefixes: Optional[Tuple[str]] = None  # List of hypertarget prefixes to assign for each file
    referenceable_text_cls: Type[BaseReferenceableText] = NumericReferenceableText

    def _to_str(self, content: Any, filename: str = None, num_file: int = 0, view_purpose: ViewPurpose = None) -> str:
        return self.get_formatted_text_and_header_references(content, filename, num_file, view_purpose)[0]

    def _get_prefix(self, num_file: int) -> str:
        return self.hypertarget_prefixes[num_file] if self.hypertarget_prefixes else None

    def get_formatted_text_and_header_references(self, content: Any, filename: str = None, num_file: int = 0,
                                                 view_purpose: ViewPurpose = None) -> Tuple[str, List[ReferencedValue]]:
        referencable_text = self._get_referencable_text(content, filename, num_file, view_purpose)
        return referencable_text.get_formatted_text_and_header_references(
            hypertarget_format=self._get_hyper_target_format(content, filename, num_file, view_purpose))

    def _convert_content_to_labeled_text(self, content: Any, filename: str = None, num_file: int = 0,
                                         view_purpose: ViewPurpose = None) -> str:
        return super()._to_str(content, filename, num_file, view_purpose)

    def _get_referencable_text(self, content: Any, filename: str = None, num_file: int = 0,
                               view_purpose: ViewPurpose = None) -> BaseReferenceableText:
        return self.referenceable_text_cls(
            text=self._convert_content_to_labeled_text(content, filename, num_file, view_purpose),
            hypertarget_prefix=self._get_prefix(num_file),
        )

    def _get_hyper_target_format(self, content: Any, filename: str = None, num_file: int = 0,
                                 view_purpose: ViewPurpose = None) -> HypertargetFormat:
        # prefix = self._get_prefix(num_file)
        # if prefix is None:
        #     return HypertargetFormat()  # no hypertargets
        return self.content_view_purpose_converter.convert_view_purpose_to_hypertarget_format(view_purpose)


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
                code_problem=CodeProblem.OutputFileContentA,
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
                code_problem=CodeProblem.OutputFileContentB,
            ))

        return issues


@dataclass(frozen=True)
class NumericTextContentOutputFileRequirement(ReferencableContentOutputFileRequirement):
    target_precision: int = NUM_DIGITS_FOR_FLOATS
    source_precision: int = 10

    def _to_str(self, content: Any, filename: str = None, num_file: int = 0, view_purpose: ViewPurpose = None) -> str:
        content = super()._to_str(content, filename, num_file, view_purpose)
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

    def get_created_files_available_for_next_steps(self) -> List[str]:
        """
        Return the names of the files created by the run, and which should be made available for the next steps.
        """
        return [filename for requirement, files_to_contents in self.items()
                for filename in files_to_contents.keys() if
                requirement.should_keep_file and requirement.should_make_available_for_next_steps]

    def get_created_files_to_requirements_and_contents(self, match_filename: str = '*',
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
                self.get_created_files_to_requirements_and_contents(match_filename, is_content=True).items()}

    def get_created_content_files(self, match_filename: str = '*') -> List[str]:
        """
        Return the names of the files created by the run, for which we collected the content.
        """
        return list(self.get_created_content_files_to_contents(match_filename).keys())

    def get_created_data_files(self, match_filename: str = '*') -> List[str]:
        """
        Return the names of the files created by the run, and which were kept, not deleted.
        """
        return list(self.get_created_files_to_requirements_and_contents(match_filename, is_content=False).keys())

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
