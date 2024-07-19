from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class FormattedSection:
    label: Optional[str]
    section: str
    is_complete: bool = True

    def to_tuple(self):
        return self.label, self.section, self.is_complete

    def to_text(self):
        if not self.is_block:
            # regular text
            return self.section
        else:
            # block
            text = f'```{self.label}{self.section}'
            if self.is_complete:
                text += '```'
            return text

    @property
    def is_block(self):
        return self.label is not None


class FormattedSections(List[FormattedSection]):
    """
    Represents a text with multiple triple-backtick sections.

    We split the text into sections.
    For example:
    text =
    '''
    Hello here is my code:
    ```python
    a = 2
    ```
    is represnted by:
    [
    (None, "\nHello here is my code:\n", True),
    ('python', "\na = 2\n", True),
    ]
    """

    @classmethod
    def from_text(cls, text: str, strip_label: bool = True) -> FormattedSections:
        """
        Create FormattedSections from text.
        strip_label: if True, then ``` python \n etc``` is converted to label='python', not ' python '
        """
        sections = text.split('```')
        is_block = True
        self = cls()
        for i, section in enumerate(sections):
            is_block = not is_block
            if section == '':
                continue
            if is_block:
                is_single_line = '\n' not in section
                text_in_quote_line = section.split('\n')[0]
                if strip_label:
                    text_in_quote_line = text_in_quote_line.strip()
                if not is_single_line and (text_in_quote_line == '' or text_in_quote_line.isalpha()):
                    label = text_in_quote_line
                    section = '\n' + '\n'.join(section.split('\n')[1:])
                else:
                    label = ''
            else:
                label = None
            is_last = i == len(sections) - 1
            is_incomplete = is_last and is_block
            self.append(FormattedSection(label, section, not is_incomplete))
        return self

    def to_text(self) -> str:
        text = ''
        for i, formatted_section in enumerate(self):
            text += formatted_section.to_text()
        return text

    def get_first_block(self) -> Optional[FormattedSection]:
        for formatted_section in self:
            if formatted_section.is_block:
                return formatted_section
        return None

    def get_last_block(self) -> Optional[FormattedSection]:
        for formatted_section in reversed(self):
            if formatted_section.is_block:
                return formatted_section
        return None

    def get_all_blocks(self) -> List[FormattedSection]:
        return [formatted_section for formatted_section in self if formatted_section.is_block]

    def is_last_block_incomplete(self):
        last_block = self.get_last_block()
        return last_block is not None and not last_block.is_complete
