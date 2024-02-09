from __future__ import annotations
import re
from dataclasses import dataclass
from enum import Enum
from functools import partial
from typing import Tuple, List, Optional, Union

TARGET = r'\hypertarget'
LINK = r'\hyperlink'


def get_numeric_value_pattern(must_follow: Optional[str] = None, allow_commas: bool = True) -> str:
    """
    Get a pattern for a numeric value that must follow a sequence of characters.
    """
    # if must_follow is None:
    #     must_follow = ''
    # if allow_commas:
    #     return fr'(?<={must_follow})(?:[-+]?\d+(?:,\d{{3}})*(?:\.\d+)?(?:e[-+]?\d+)?|\d{{1,3}}(?:,\d{{3}})+)(?!\d)'
    # return fr'(?<={must_follow})[+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?'

    if must_follow is None:
        must_follow = ''
    else:
        must_follow = fr'(?<={must_follow})'
    if allow_commas:
        pattern = r'(?:[-+]?\d+(?:,\d{3})*(?:\.\d+)?(?:e[-+]?\d+)?|\d{1,3}(?:,\d{{3}})+)(?!\d)'
    else:
        pattern = r'[-+]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?'
    return must_follow + pattern


numeric_values_in_products_pattern = get_numeric_value_pattern(must_follow=r'[$,{<=\s\n\(\[]', allow_commas=True)
numeric_values_in_response_pattern = get_numeric_value_pattern(must_follow=r'[$,{<=\s\n\(\[]', allow_commas=True)


def get_hyperlink_pattern(is_target: bool = False) -> str:
    """
    Get a pattern for a hyperlink.
    """
    command = TARGET if is_target else LINK
    return fr'\{command}{{(?P<reference>[^}}]*)}}{{(?P<value>[^}}]*)}}'


@dataclass
class ReferencedValue:
    """
    A numeric value with a reference to it.
    """
    value: str
    reference: Optional[str] = None  # if None for un-referenced numeric values
    is_target: bool = False

    @property
    def command(self) -> str:
        return TARGET if self.is_target else LINK

    def to_str(self, hypertarget_position: HypertargetPosition) -> str:
        if hypertarget_position == HypertargetPosition.NONE or self.reference is None:
            return self.value
        if hypertarget_position == HypertargetPosition.WRAP:
            return fr'{self.command}{{{self.reference}}}{{{self.value}}}'
        if hypertarget_position == HypertargetPosition.HEADER:
            return self.value
        if hypertarget_position == HypertargetPosition.RAISED:
            return fr'\raisebox{{2ex}}{{{self.command}{{{self.reference}}}{{}}}}{self.value}'
        raise ValueError(f'Invalid hypertarget position: {hypertarget_position}')

    def __str__(self):
        return self.to_str(HypertargetPosition.WRAP)

    def get_numeric_value_and_is_percent(self) -> Tuple[Optional[str], bool]:
        """
        Get the numeric value from a string.
        """
        value = self.value.strip()
        pattern = get_numeric_value_pattern()
        if re.fullmatch(pattern, value.strip()):
            return value, False
        for add in [r'\%', '%', r' \%', ' %']:
            if bool(re.fullmatch(pattern + re.escape(add), value)):
                return value[:-(len(add))], True
        return None, False

    def to_float(self) -> Optional[float]:
        value, is_percent = self.get_numeric_value_and_is_percent()
        if value is None:
            return None
        value = float(value.strip().replace(',', ''))
        return value / 100 if is_percent else value


@dataclass
class ReferencableText:
    """
    A text which can be converted to hypertargeted text/
    """
    text: str
    hypertarget_prefix: Optional[str] = None  # if None, no hypertargets are created

    def __str__(self):
        return self.text

    def get_text(self, hypertarget_position: HypertargetPosition) -> str:
        if not hypertarget_position or self.hypertarget_prefix is None:
            return self.text
        return create_hypertargets_to_numeric_values(self.text, prefix=self.hypertarget_prefix)[0]

    def get_references(self) -> List[ReferencedValue]:
        if self.hypertarget_prefix is None:
            return []
        return create_hypertargets_to_numeric_values(self.text, prefix=self.hypertarget_prefix)[1]


class HypertargetPosition(Enum):
    """
    Whether and and which position to put hypertargets.
    """
    NONE = 0  # Header ... value
    WRAP = 1  # Header ... \hypertarget{target}{value}
    HEADER = 2  # \hypertarget{target}Header ... value
    RAISED = 3  # Header ... \raisebox{2ex}{\hypertarget{target}{}}value

    def __bool__(self):
        return self != HypertargetPosition.NONE


def hypertarget_if_referencable_text(text: Union[str, ReferencableText], hypertarget_position: HypertargetPosition
                                     ) -> str:
    """
    Create hypertargets if the text is referencable, otherwise return the text.
    """
    if isinstance(text, ReferencableText):
        return text.get_text(hypertarget_position)
    return text


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


def create_hypertargets_to_numeric_values(text: str, prefix: Optional[str] = None,
                                          pattern: str = numeric_values_in_products_pattern,
                                          hypertarget_position: HypertargetPosition = HypertargetPosition.NONE,
                                          ) -> Tuple[str, List[ReferencedValue]]:
    """
    Find all numeric values in text and create references to them.
    Replace the numeric values with the references.
    Return the text with the references and the references.
    """

    if prefix is None or not hypertarget_position:
        return text, []

    def replace_numeric_value_with_hypertarget(match, prefix_):
        value = match.group(0)
        in_line_letter = _num_to_letters(len(references_per_line) + 1)
        reference = ReferencedValue(value=value, reference=f'{prefix_}{in_line_letter}', is_target=True)
        references_per_line.append(reference)
        return reference.to_str(hypertarget_position)

    references = []
    lines = text.split('\n')
    num_line_with_ref = 0
    for i, line in enumerate(lines):
        references_per_line = []
        line = re.sub(pattern,
                      partial(replace_numeric_value_with_hypertarget, prefix_=f'{prefix}{num_line_with_ref}'), line)
        if references_per_line:
            num_line_with_ref += 1
            lines[i] = line
            references.extend(references_per_line)
    text = '\n'.join(lines)
    if hypertarget_position == HypertargetPosition.HEADER:
        text = ''.join([str(reference) for reference in references]) + text
    return text, references


def find_hyperlinks(text: str, is_targets: bool = False) -> List[ReferencedValue]:
    """
    Find all references in the text.
    """
    pattern = get_hyperlink_pattern(is_targets)
    references = []
    for match in re.finditer(pattern, text):
        references.append(ReferencedValue(value=match.group('value'), reference=match.group('reference'),
                                          is_target=False))
    return references


def replace_hyperlinks_with_values(text: str, is_targets: bool = False) -> str:
    """
    Replace all references in the text with the referenced values.
    """
    def replace_hyperlink_with_value(match):
        return match.group('value')

    pattern = get_hyperlink_pattern(is_targets)
    return re.sub(pattern, replace_hyperlink_with_value, text)


def find_numeric_values(text: str, remove_hyperlinks: bool = True,
                        pattern: str = numeric_values_in_response_pattern,
                        ) -> List[str]:
    """
    Find all numeric values in the text that are not referenced.
    """
    text = ' ' + text + ' '
    # remove all references from the text
    if remove_hyperlinks:
        text = re.sub(get_hyperlink_pattern(is_target=False), '', text)
    # find all numeric values
    return re.findall(pattern, text)


def find_matching_reference(query: ReferencedValue,
                            references: List[ReferencedValue]) -> Optional[ReferencedValue]:
    """
    Find the reference in references that matches the query.
    We assume that there is a unique match.
    Return None if no match was found.
    """
    for reference in references:
        if query.reference == reference.reference:
            return reference
    return None
