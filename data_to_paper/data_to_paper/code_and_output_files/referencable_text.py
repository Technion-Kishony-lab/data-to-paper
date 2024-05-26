import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Tuple, Union

from data_to_paper.code_and_output_files.file_view_params import \
    ContentViewParams, ContentView, ContentViewPurposeConverter
from data_to_paper.code_and_output_files.ref_numeric_values import HypertargetPosition, \
    numeric_values_in_products_pattern, ReferencedValue

EXTS_TO_LABELS = {
    '.tex': 'latex',
    '.txt': 'output',
    '.csv': 'csv',
}


def _num_to_letters(num: int) -> str:
    """
    Convert a number to letters.
    1 -> a, 2 -> b, 3 -> c, ...
    200 -> gv
    """
    letters = ''
    while num > 0:
        num, remainder = divmod(num - 1, 26)
        letters = chr(ord('a') + remainder) + letters
    return letters


def convert_str_to_latex_label(text: str, prefix: str = 'label') -> str:
    """
    Convert str, like filename, into valid latex hypertarget label
    """
    return f'{prefix}-{text.replace(".", "-").replace("_", "-")}'


@dataclass
class BaseReferenceableText:
    """
    A text which can be converted to hypertargeted text
    """
    hypertarget_prefix: Optional[str] = None  # if None, no hypertargets are created
    filename: Optional[str] = None
    content_view_purpose_converter: ContentViewPurposeConverter = field(default_factory=ContentViewPurposeConverter)

    def get_header_label(self) -> str:
        if self.filename:
            return convert_str_to_latex_label(self.filename, 'file')
        if self.hypertarget_prefix:
            return self.hypertarget_prefix
        raise ValueError('Either filename or hypertarget_prefix should be set')

    def _get_text_and_references(self, content_view_params: ContentViewParams) -> Tuple[str, List[ReferencedValue]]:
        raise NotImplementedError

    def _wrap_as_block(self, content: str):
        label = EXTS_TO_LABELS.get(Path(self.filename).suffix, 'output')
        return f'"{self.filename}":\n```{label}\n{content}\n```\n'

    def get_hypertarget_text_with_header(self, content_view: ContentView) -> str:
        view_params = self.content_view_purpose_converter.convert_content_view_to_params(content_view)
        content, references = self.get_hypertarget_text_and_header_references(content_view)
        return '\n'.join(reference.to_str(view_params.hypertarget_format) for reference in references) + content

    def get_hypertarget_text_and_header_references(self, content_view: ContentView
                                                   ) -> Tuple[str, List[ReferencedValue]]:
        view_params = self.content_view_purpose_converter.convert_content_view_to_params(content_view)
        content, references = self._get_text_and_references(view_params)
        if view_params.is_block:
            content = self._wrap_as_block(content)
        if view_params.with_hyper_header:
            header_references = [ReferencedValue(label=self.get_header_label(), value='', is_target=True)]
        else:
            header_references = []
        if view_params.hypertarget_format.position == HypertargetPosition.HEADER:
            header_references.extend(references)
        return content, header_references


@dataclass
class FromTextReferenceableText(BaseReferenceableText):
    """
    A text which can be converted to hypertargeted text
    """
    text: str = ''
    pattern: str = r''

    def _get_reference(self, match, reference_num, line_no, line_no_with_ref, in_line_number) -> ReferencedValue:
        raise NotImplementedError

    def _get_text_and_references(self, content_view_params: Optional[ContentViewParams] = None
                                 ) -> Tuple[str, List[ReferencedValue]]:
        """
        Find all numeric values in text and create references to them.
        Replace the numeric values with the references.
        Return the text with the references and the references.
        """

        def replace_numeric_value_with_hypertarget(match):
            nonlocal reference_num, line_no, line_no_with_ref
            in_line_number = len(references_per_line)
            reference = self._get_reference(match, reference_num, line_no, line_no_with_ref, in_line_number)
            references_per_line.append(reference)
            reference_num = reference_num + 1
            if content_view_params:
                return reference.to_str(content_view_params.hypertarget_format)
            else:
                return reference.value

        if self.hypertarget_prefix is None:
            return self.text, []
        reference_num = 0
        references = []
        lines = self.text.split('\n')
        line_no_with_ref = 0
        for line_no, line in enumerate(lines):
            references_per_line = []
            line = re.sub(self.pattern, replace_numeric_value_with_hypertarget, line)
            if references_per_line:
                line_no_with_ref += 1
                lines[line_no] = line
                references.extend(references_per_line)
        text = '\n'.join(lines)
        return text, references


@dataclass
class NumericReferenceableText(FromTextReferenceableText):
    """
    A text whose numeric values can be converted to hypertargets.
    """
    pattern: str = numeric_values_in_products_pattern

    def _get_reference(self, match, reference_num, line_no, line_no_with_ref, in_line_number):
        return ReferencedValue(
            label=self._get_label(match, reference_num, line_no, line_no_with_ref, in_line_number),
            value=self._get_value(match, reference_num, line_no, line_no_with_ref, in_line_number),
            is_target=True,
        )

    def _get_label(self, match, reference_num, line_no, line_no_with_ref, in_line_number):  # noqa
        in_line_letter = _num_to_letters(in_line_number + 1)
        return f'{self.hypertarget_prefix}{line_no_with_ref}{in_line_letter}'

    def _get_value(self, match, reference_num, line_no, line_no_with_ref, in_line_number):  # noqa
        return match.group(0)


@dataclass
class ListReferenceableText(FromTextReferenceableText):
    """
    A text whose list items can be converted to hypertargets.
    """
    reference_list: List[ReferencedValue] = field(default_factory=list)

    def _get_reference(self, match, reference_num, line_no, line_no_with_ref, in_line_number):
        return self.reference_list[reference_num]


def hypertarget_if_referencable_text(text: Union[str, BaseReferenceableText],
                                     content_view: ContentView,
                                     ) -> str:
    """
    Create hypertargets if the text is referencable, otherwise return the text.
    """
    if isinstance(text, BaseReferenceableText):
        return text.get_hypertarget_text_with_header(content_view)
    return text
