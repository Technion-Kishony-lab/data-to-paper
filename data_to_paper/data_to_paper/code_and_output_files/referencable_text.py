from __future__ import annotations
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Tuple, Union, Any

from data_to_paper.base_products.product import ValueProduct, Product
from data_to_paper.code_and_output_files.file_view_params import ViewPurpose, ContentViewPurposeConverter
from data_to_paper.code_and_output_files.ref_numeric_values import HypertargetPosition, \
    numeric_values_in_products_pattern, ReferencedValue, HypertargetFormat
from data_to_paper.utils.text_formatting import wrap_text_with_triple_quotes

EXTS_TO_LABELS = {
    '.tex': 'latex',
    '.txt': 'output',
    '.csv': 'csv',
}


@dataclass
class ReferencableTextProduct(Product):
    referencable_text: BaseReferenceableText = None
    name: str = None
    block_label: Optional[Union[bool, str]] = None  # True - use auto label; str, use this label; None - no label
    header_hypertarget_prefix: Optional[str] = None
    header_hypertarget_label: Optional[str] = None
    header_hyperlink_label: Optional[str] = None
    content_view_purpose_converter: Optional[ContentViewPurposeConverter] = field(default_factory=ContentViewPurposeConverter)

    @property
    def hypertarget_prefix(self):
        return self.referencable_text.hypertarget_prefix

    def is_valid(self):
        return self.referencable_text is not None

    def _get_formatted_content(self, view_purpose: ViewPurpose) -> str:
        view_params = self.content_view_purpose_converter.convert_view_purpose_to_view_params(view_purpose)
        hypertarget_format = view_params.hypertarget_format
        content, _ = self._get_formatted_text_and_header_references(hypertarget_format)
        return content

    def get_header(self, **kwargs) -> str:
        view_purpose: ViewPurpose = kwargs.get('view_purpose')
        view_params = self.content_view_purpose_converter.convert_view_purpose_to_view_params(view_purpose)
        hypertarget_format = view_params.hypertarget_format
        _, references = self._get_formatted_text_and_header_references(hypertarget_format)
        header = super().get_header()
        if view_params.with_hyper_header:
            header_hyperlink_label = self.get_header_hyperlink_label()
            header_hypertarget_label = self.get_header_hypertarget_label()
            if header_hyperlink_label:
                header = ReferencedValue(label=header_hyperlink_label, value=header, is_target=False).to_str()
            if header_hypertarget_label:
                references.append(ReferencedValue(label=header_hypertarget_label, value='', is_target=True))
        header = '\n'.join(reference.to_str(hypertarget_format) for reference in references) + header
        return header

    def _get_content_as_markdown(self, level: int, **kwargs) -> str:
        view_purpose: ViewPurpose = kwargs.get('view_purpose')
        content = self._get_formatted_content(view_purpose)
        content = self._process_content(content)
        return content

    def _process_content(self, content: str) -> str:
        if self.block_label:
            if self.block_label is True:
                block_label = EXTS_TO_LABELS.get(Path(self.name).suffix, 'output')
            else:
                block_label = self.block_label
            return wrap_text_with_triple_quotes(content, block_label)
        return content

    def get_header_hypertarget_label(self) -> str:
        if self.header_hyperlink_label:
            label = self.header_hyperlink_label
        elif self.get_header():
            label = self.get_header()
        else:
            raise ValueError('Either header_hypertarget_prefix or name should be set')
        return convert_str_to_latex_label(label, self.header_hypertarget_prefix)

    def get_header_hyperlink_label(self) -> Optional[str]:
        if self.header_hyperlink_label:
            return self.header_hyperlink_label
        return None

    def _get_formatted_text_and_header_references(self, hypertarget_format: HypertargetFormat
                                                  ) -> Tuple[str, List[ReferencedValue]]:
        return self.referencable_text.get_formatted_text_and_header_references(hypertarget_format)


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


def convert_str_to_latex_label(text: str, prefix: Optional[str] = None) -> str:
    """
    Convert str, like filename, into valid latex hypertarget label
    """
    if prefix is not None:
        text = f'{prefix}-{text}'
    return text.replace(".", "-").replace("_", "-")


@dataclass
class BaseReferenceableText:
    """
    A text which can be converted to hypertargeted text
    """
    hypertarget_prefix: Optional[str] = None  # if None, no hypertargets are created

    def get_formatted_text_and_references(self, hypertarget_format: HypertargetFormat
                                          ) -> Tuple[str, List[ReferencedValue]]:
        raise NotImplementedError

    def get_formatted_text(self, hypertarget_format: HypertargetFormat) -> str:
        return self.get_formatted_text_and_references(hypertarget_format)[0]

    def get_formatted_text_and_header_references(self, hypertarget_format: HypertargetFormat
                                                 ) -> Tuple[str, List[ReferencedValue]]:
        content, references = self.get_formatted_text_and_references(hypertarget_format)
        if hypertarget_format.is_hypertarget_position_header():
            return content, references
        return content, []


@dataclass
class FromTextReferenceableText(BaseReferenceableText):
    """
    A text which can be converted to hypertargeted text
    """
    text: str = ''
    pattern: str = r''

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

    def get_formatted_text_and_references(self, hypertarget_format: HypertargetFormat) -> Tuple[str, List[ReferencedValue]]:
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
            if hypertarget_format:
                return reference.to_str(hypertarget_format)
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


@dataclass
class ListReferenceableText(FromTextReferenceableText):
    """
    A text whose list items can be converted to hypertargets.
    """
    reference_list: List[ReferencedValue] = field(default_factory=list)

    def _get_reference(self, match, reference_num, line_no, line_no_with_ref, in_line_number):
        return self.reference_list[reference_num]


def hypertarget_if_referencable_text_product(text: Union[str, ReferencableTextProduct],
                                             view_purpose: ViewPurpose, **kwargs) -> str:
    """
    Create hypertargets if the text is a ReferencableTextProduct, otherwise return the text.
    """
    if isinstance(text, ReferencableTextProduct):
        return text.as_markdown(view_purpose=view_purpose, **kwargs)
    return text


@dataclass
class LabeledNumericReferenceableText(FromTextReferenceableText):
    """
    A text whose labeled numeric values can be converted to hypertargets.
    Numeric values should be labeled with @@<...>@@.
    """
    pattern: str = r'@@<(.+?)>@@'

    def _get_value(self, match, reference_num, line_no, line_no_with_ref, in_line_number):  # noqa
        return match.group(0)[3:-3]


def label_numeric_value(text: str) -> str:
    return '@@<' + text + '>@@'
