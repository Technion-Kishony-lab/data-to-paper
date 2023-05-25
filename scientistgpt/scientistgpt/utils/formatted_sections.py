from dataclasses import dataclass
from typing import List, Optional


@dataclass
class FormattedSection:
    label: Optional[str]
    section: str

    def to_tuple(self):
        return self.label, self.section


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
    def __init__(self, *args, is_complete: bool = True, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_complete = is_complete

    @classmethod
    def from_text(cls, text: str, strip_label: bool = True):

        sections = text.split('```')
        is_block = True
        self = cls()
        for section in sections:
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
                label = None
            self.append(FormattedSection(label, section))
        self.is_complete = not is_block
        return self

    def to_text(self) -> str:
        text = ''
        for i, formatted_section in enumerate(self):
            label, section = formatted_section.to_tuple()
            if label is not None:
                text += f'```{label}'
            text += section
            if label is not None and (self.is_complete or i < len(self) - 1):
                text += '```'
        return text
