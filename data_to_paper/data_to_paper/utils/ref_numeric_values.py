from __future__ import annotations
import re
from dataclasses import dataclass
from functools import partial
from typing import Tuple, List, Optional, Union

TARGET = r'\hypertarget'
REFERENCE = r'\hyperlink'


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

# regex pattern to match \hyperlink{reference}{value}
hyperlink_pattern = fr'\{REFERENCE}{{(?P<reference>[^}}]*)}}{{(?P<value>[^}}]*)}}'


@dataclass
class ReferencedValue:
    """
    A numeric value with a reference to it.
    """
    value: str
    reference: Optional[str] = None  # if None for un-referenced numeric values
    is_target: bool = False

    def __str__(self):
        if self.reference is None:
            return self.value
        if self.is_target:
            command = TARGET
        else:
            command = REFERENCE
        return fr'{command}{{{self.reference}}}{{{self.value}}}'

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

    def get_text(self, should_hypertarget: bool = True) -> str:
        if not should_hypertarget or self.hypertarget_prefix is None:
            return self.text
        return create_hypertargets_to_numeric_values(self.text, prefix=self.hypertarget_prefix)[0]

    def get_references(self) -> List[ReferencedValue]:
        if self.hypertarget_prefix is None:
            return []
        return create_hypertargets_to_numeric_values(self.text, prefix=self.hypertarget_prefix)[1]


def hypertarget_if_referencable_text(text: Union[str, ReferencableText], should_hypertarget: bool = True) -> str:
    """
    Create hypertargets if the text is referencable, otherwise return the text.
    """
    if isinstance(text, ReferencableText):
        return text.get_text(should_hypertarget)
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
                                          pattern: str = numeric_values_in_products_pattern
                                          ) -> Tuple[str, List[ReferencedValue]]:
    """
    Find all numeric values in text and create references to them.
    Replace the numeric values with the references.
    Return the text with the references and the references.
    """

    if prefix is None:
        return text, []

    def replace_numeric_value_with_hypertarget(match, prefix_):
        value = match.group(0)
        in_line_letter = _num_to_letters(len(references_per_line) + 1)
        reference = ReferencedValue(value=value, reference=f'{prefix_}{in_line_letter}', is_target=True)
        references_per_line.append(reference)
        return str(reference)

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
    return text, references


def find_hyperlinks(text: str) -> List[ReferencedValue]:
    """
    Find all references in the text.
    """
    references = []
    for match in re.finditer(hyperlink_pattern, text):
        references.append(ReferencedValue(value=match.group('value'), reference=match.group('reference'),
                                          is_target=False))
    return references


def replace_hyperlinks_with_values(text: str) -> str:
    """
    Replace all references in the text with the referenced values.
    """
    def replace_hyperlink_with_value(match):
        return match.group('value')

    return re.sub(hyperlink_pattern, replace_hyperlink_with_value, text)


def find_numeric_values(text: str, remove_hyperlinks: bool = True,
                        pattern: str = numeric_values_in_response_pattern,
                        ) -> List[str]:
    """
    Find all numeric values in the text that are not referenced.
    """
    text = ' ' + text + ' '
    # remove all references from the text
    if remove_hyperlinks:
        text = re.sub(hyperlink_pattern, '', text)
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
