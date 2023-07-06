from dataclasses import dataclass
from typing import Optional

from data_to_paper.utils.formatted_sections import FormattedSections


@dataclass
class FailedExtractingBlock(Exception):
    content_name: str  # e.g. "code", "latex"
    requested_label: Optional[str]  # e.g. "python", "latex"


@dataclass
class NoBlocksFailedExtractingBlock(FailedExtractingBlock):
    def __str__(self):
        return f"You did not send any {self.content_name} block.\n" \
               f"Please try again, making sure your {self.content_name} is enclosed within triple-backticks."


@dataclass
class MultiBlocksFailedExtractingBlock(FailedExtractingBlock):
    num_blocks: int

    def __str__(self):
        return f"Please send your {self.content_name} as a single triple-quoted block."


@dataclass
class IncompleteBlockFailedExtractingBlock(FailedExtractingBlock):
    def __str__(self):
        return f"Your sent incomplete {self.content_name} block. Please resend."


@dataclass
class WrongLabelFailedExtractingBlock(FailedExtractingBlock):
    label: str

    def __str__(self):
        return f'Your sent a "{self.label}" block. ' \
               f'Please send your {self.content_name} as a "{self.requested_label}" block.'


def add_label_to_first_triple_quotes_if_missing(content: str, requested_label: str) -> str:
    """
    Add "python" to triple quotes if missing.
    """
    formatted_sections = FormattedSections.from_text(content)
    first_block = formatted_sections.get_first_block()
    if first_block is not None:
        label = first_block.label
        if requested_label is not True and label.lower() in ['', requested_label]:
            first_block.label = requested_label
    return formatted_sections.to_text()


def extract_content_of_triple_quote_block(text: str, content_name: str, requested_label: Optional[str] = None) -> str:
    formatted_sections = FormattedSections.from_text(text)
    block_sections = formatted_sections.get_all_blocks()
    if len(block_sections) == 0:
        raise NoBlocksFailedExtractingBlock(content_name, requested_label)
    if len(block_sections) > 1:
        raise MultiBlocksFailedExtractingBlock(content_name, requested_label, len(block_sections))
    block_section = block_sections[0]
    if not block_section.is_complete:
        raise IncompleteBlockFailedExtractingBlock(content_name, requested_label)
    if requested_label is not None and block_section.label and block_section.label != requested_label:
        raise WrongLabelFailedExtractingBlock(content_name, requested_label, block_section.label)
    return block_section.section


def extract_code_from_text(text: str) -> str:
    """
    Extract Python code from text.
    Raise FailedExtractingBlock if the code cannot be extracted.
    """
    return extract_content_of_triple_quote_block(text, content_name='code', requested_label="python")
