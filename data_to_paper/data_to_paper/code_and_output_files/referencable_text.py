import re
from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Union

from data_to_paper.code_and_output_files.ref_numeric_values import HypertargetPosition, numeric_values_in_products_pattern, \
    ReferencedValue


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


@dataclass
class BaseReferenceableText:
    """
    A text which can be converted to hypertargeted text/
    """
    hypertarget_prefix: Optional[str] = None  # if None, no hypertargets are created
    default_hypertarget_position: HypertargetPosition = HypertargetPosition.NONE

    def __str__(self):
        return self.get_text(self.default_hypertarget_position)

    def get_text(self, hypertarget_position: HypertargetPosition) -> str:
        raise NotImplementedError

    def get_references(self) -> List[ReferencedValue]:
        raise NotImplementedError


@dataclass
class FromTextReferenceableText(BaseReferenceableText):
    """
    A text which can be converted to hypertargeted text/
    """
    text: str = ''
    pattern: str = r''

    def get_text(self, hypertarget_position: HypertargetPosition) -> str:
        return self._create_hypertargets_to_numeric_values(hypertarget_position)[0]

    def get_references(self) -> List[ReferencedValue]:
        return self._create_hypertargets_to_numeric_values()[1]

    def _get_reference(self, match, reference_num, line_no, line_no_with_ref, in_line_number):
        raise NotImplementedError

    def _create_hypertargets_to_numeric_values(self,
                                               hypertarget_position: HypertargetPosition = HypertargetPosition.NONE,
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
            return reference.to_str(hypertarget_position)

        if self.hypertarget_prefix is None or not hypertarget_position:
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
        if hypertarget_position == HypertargetPosition.HEADER:
            text = ''.join([str(reference) for reference in references]) + text
        return text, references


@dataclass
class NumericReferenceableText(FromTextReferenceableText):
    """
    A text which can be converted to hypertargeted text/
    """
    pattern: str = numeric_values_in_products_pattern

    def _get_reference(self, match, reference_num, line_no, line_no_with_ref, in_line_number):
        return ReferencedValue(
            label=self._get_label(match, reference_num, line_no, line_no_with_ref, in_line_number),
            value=self._get_value(match, reference_num, line_no, line_no_with_ref, in_line_number),
            is_target=True,
        )

    def _get_label(self, match, reference_num, line_no, line_no_with_ref, in_line_number):
        in_line_letter = _num_to_letters(in_line_number + 1)
        return f'{self.hypertarget_prefix}{line_no_with_ref}{in_line_letter}'

    def _get_value(self, match, reference_num, line_no, line_no_with_ref, in_line_number):
        return match.group(0)


@dataclass
class ListReferenceableText(FromTextReferenceableText):
    reference_list: List[ReferencedValue] = field(default_factory=list)

    def _get_reference(self, match, reference_num, line_no, line_no_with_ref, in_line_number):
        return self.reference_list[reference_num]


def hypertarget_if_referencable_text(text: Union[str, BaseReferenceableText], hypertarget_position: HypertargetPosition
                                     ) -> str:
    """
    Create hypertargets if the text is referencable, otherwise return the text.
    """
    if isinstance(text, BaseReferenceableText):
        return text.get_text(hypertarget_position)
    return text
