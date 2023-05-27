from dataclasses import dataclass

from scientistgpt.utils.formatted_sections import FormattedSections


@dataclass
class FailedExtractingCode(Exception):
    pass


@dataclass
class NoBlocksFailedExtractingCode(FailedExtractingCode):
    def __str__(self):
        return "You did not send any code.\n" \
               "Please try again, making sure your code is enclosed within triple-backticks."


@dataclass
class MultiBlocksFailedExtractingCode(FailedExtractingCode):
    num_blocks: int

    def __str__(self):
        return "Please send your code as a single code block."


@dataclass
class IncompleteBlockFailedExtractingCode(FailedExtractingCode):
    def __str__(self):
        return "Your sent incomplete code. Please resend."


@dataclass
class WrongLabelFailedExtractingCode(FailedExtractingCode):
    label: str

    def __str__(self):
        return f'Your sent a "{self.label}" block. Please send your code as a "python" block.'


def add_python_label_to_first_triple_quotes_if_missing(content: str):
    """
    Add "python" to triple quotes if missing.
    """
    formatted_sections = FormattedSections.from_text(content)
    first_block = formatted_sections.get_first_block()
    if first_block is not None:
        label = first_block.label
        if (label == '' or label.lower() == 'python') and not first_block.is_single_line:
            first_block.label = 'python'
    return formatted_sections.to_text()


def extract_code_from_text(text: str) -> str:
    """
    Extract Python code from text.
    Raise FailedExtractingCode if the code cannot be extracted.
    """
    formatted_sections = FormattedSections.from_text(text)
    block_sections = formatted_sections.get_all_blocks()
    if len(block_sections) == 0:
        raise NoBlocksFailedExtractingCode()
    if len(block_sections) > 1:
        raise MultiBlocksFailedExtractingCode(len(block_sections))
    block_section = block_sections[0]
    if not block_section.is_complete:
        raise IncompleteBlockFailedExtractingCode()
    if block_section.label != 'python':
        raise WrongLabelFailedExtractingCode(block_section.label)
    return block_section.section
