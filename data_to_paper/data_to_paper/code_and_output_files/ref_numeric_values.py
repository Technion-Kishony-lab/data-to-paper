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
    label: Optional[str] = None  # if None for un-referenced numeric values
    is_target: bool = False

    @property
    def command(self) -> str:
        return TARGET if self.is_target else LINK

    def to_str(self, hypertarget_position: HypertargetPosition) -> str:
        if hypertarget_position == HypertargetPosition.NONE or self.label is None:
            return self.value
        if hypertarget_position == HypertargetPosition.WRAP:
            return fr'{self.command}{{{self.label}}}{{{self.value}}}'
        if hypertarget_position == HypertargetPosition.HEADER:
            return self.value
        if hypertarget_position == HypertargetPosition.RAISED:
            return fr'\raisebox{{2ex}}{{{self.command}{{{self.label}}}{{}}}}{self.value}'
        if hypertarget_position == HypertargetPosition.RAISED_ESCAPE:
            return fr'(*@{self.to_str(HypertargetPosition.RAISED)}@*)'
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


class HypertargetPosition(Enum):
    """
    Whether and and which position to put hypertargets.
    """
    NONE = 0  # Header ... value
    WRAP = 1  # Header ... \hypertarget{target}{value}
    HEADER = 2  # \hypertarget{target}Header ... value
    RAISED = 3  # Header ... \raisebox{2ex}{\hypertarget{target}{}}value
    RAISED_ESCAPE = 4  # Header ...  (*@\raisebox{2ex}{\hypertarget{target}{}}value@*)

    def __bool__(self):
        return self != HypertargetPosition.NONE


def find_hyperlinks(text: str, is_targets: bool = False) -> List[ReferencedValue]:
    """
    Find all references in the text.
    """
    pattern = get_hyperlink_pattern(is_targets)
    references = []
    for match in re.finditer(pattern, text):
        references.append(ReferencedValue(value=match.group('value'), label=match.group('reference'),
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
        if query.label == reference.label:
            return reference
    return None
