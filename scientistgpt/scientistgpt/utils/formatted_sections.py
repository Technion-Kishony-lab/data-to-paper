from dataclasses import dataclass
from typing import List, Optional


@dataclass
class FormattedSection:
    label: Optional[str]
    section: str
    is_complete: bool = True
    is_single_line: bool = False

    def to_tuple(self):
        return self.label, self.section, self.is_complete, self.is_single_line


class FormattedSections(List[FormattedSection]):
    """
    Represents a text with multiple triple-quoted sections.

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
    def from_text(cls, text: str, strip_label: bool = True):

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
                if not is_single_line and ' ' not in text_in_quote_line:
                    label = text_in_quote_line
                    section = '\n' + '\n'.join(section.split('\n')[1:])
                else:
                    label = ''
            else:
                is_single_line = None
                label = None
            is_last = i == len(sections) - 1
            is_incomplete = is_last and is_block
            self.append(FormattedSection(label, section, not is_incomplete, is_single_line))
        return self

    def to_text(self) -> str:
        text = ''
        for i, formatted_section in enumerate(self):
            label, section, is_complete, _ = formatted_section.to_tuple()
            if label is None:
                # regular text
                text += section
            else:
                # block
                text += f'```{label}{section}'
                if is_complete:
                    text += '```'
        return text

    def get_first_block(self) -> Optional[FormattedSection]:
        for formatted_section in self:
            if formatted_section.label is not None:
                return formatted_section
        return None

    def get_last_block(self) -> Optional[FormattedSection]:
        for formatted_section in reversed(self):
            if formatted_section.label is not None:
                return formatted_section
        return None

    def get_all_blocks(self) -> List[FormattedSection]:
        return [formatted_section for formatted_section in self if formatted_section.label is not None]

    def is_last_block_incomplete(self):
        last_block = self.get_last_block()
        return last_block is not None and not last_block.is_complete
