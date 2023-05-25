from dataclasses import dataclass
from typing import List, Tuple, Optional, NamedTuple

FROM_OPEN_BRACKET_TO_CLOSE_BRACKET = {'[': ']', '{': '}', '(': ')'}


@dataclass
class FormattedSection:
    label: Optional[str]
    section: str
    is_complete: bool

    def to_tuple(self):
        return self.label, self.section, self.is_complete


def extract_text_between_tags(text: str, left_tag: str, right_tag: str = None, leave_tags: bool = False):
    """
    Extract text between two tags.
    If the right tag is None, then extract text from the left tag to the end of the text
    We also take in account nested brackets.
    """
    optional_brackets = {'[': ']', '{': '}', '(': ')'}
    left_bracket = left_tag[-1]
    if right_tag is not None:
        right_bracket = right_tag[-1]
        if left_bracket not in optional_brackets.keys() or right_bracket != optional_brackets[left_bracket]:
            # just find the first instance of the right tag and return the text between the left tag and the right tag
            start = text.find(left_tag)
            if start == -1:
                raise ValueError(f'Could not find left tag {left_tag} in text')
            end = text.find(right_tag, start + len(left_tag))
            if end == -1:
                raise ValueError(f'Could not find left tag {right_tag} in text')
            if end - start - len(left_tag) == 0:
                raise ValueError(f'Could not find left tag {left_tag} in text')
            if leave_tags:
                return text[start:end + len(right_tag)]
            return text[start + len(left_tag):end]
        else:
            # use extract_text_between_brackets to extract the text between the brackets
            if leave_tags:
                return left_tag + extract_text_between_brackets(text, left_bracket) + right_tag
            return extract_text_between_brackets(text, left_bracket)
    else:
        # right tag is None, so we return the text from the left tag to the end of the text
        start = text.find(left_tag)
        if start == -1:
            raise ValueError(f'Could not find left tag {left_tag} in text')
        if leave_tags:
            return left_tag + text[start + len(left_tag):]
        return text[start + len(left_tag):]


def extract_text_between_brackets(text: str, open_bracket: str, leave_brackets: bool = False):
    """
    use stack to find matching closing bracket for the first open bracket, use stack to find matching closing bracket.
    return the text between the first open bracket and the matching closing bracket without the brackets.
    """
    start = text.find(open_bracket)
    if start == -1:
        raise ValueError(f'Could not find open bracket {open_bracket} in text')
    end = start + 1
    stack = [open_bracket]
    while len(stack) > 0:
        if end == len(text):
            raise ValueError(f'Could not find matching closing bracket for open bracket {open_bracket} in text')
        if text[end] == open_bracket:
            stack.append(open_bracket)
        elif text[end] == FROM_OPEN_BRACKET_TO_CLOSE_BRACKET[open_bracket]:
            stack.pop()
        end += 1
    if leave_brackets:
        return text[start:end]
    return text[start + 1:end - 1]


def extract_first_lines(text: str, num_lines: int = 1):
    """
    Extract the first num_lines lines from the text.
    """
    return '\n'.join(text.splitlines()[:num_lines])


def _extract_to_nearest(text: str, max_length: int, char: str = '\n'):
    """
    Extract the text from the beginning of the text to the nearest char before end.
    If no char is found, extract the text from the beginning of the text to end.
    if max_length is negative, extract the text from the end of the text to the nearest char before end.
    """
    if abs(max_length) > len(text):
        return text
    if max_length >= 0:
        text = text[:max_length]
        end = text.rfind(char) if char in text else max_length
        return text[:end]
    else:
        text = text[max_length:]
        end = text.find(char) + 1 if char in text else max_length
        return text[end:]


def extract_to_nearest_newline(text: str, end: int):
    """
    Extract the text from the beginning of the text to the nearest newline before end.
    If no newline is found, extract the text from the beginning of the text to end.
    """
    return _extract_to_nearest(text, end, '\n')


def extract_to_nearest_space(text: str, end: int):
    """
    Extract the text from the beginning of the text to the nearest space before end.
    If no space is found, extract the text from the beginning of the text to end.
    """
    return _extract_to_nearest(text, end, ' ')


def get_dot_dot_dot_text(text: str, start: int, end: int):
    """
    Get the text from the beginning of the text to the nearest space before start and from the nearest space after end
    to the end of the text.
    """
    fill = ' ... '
    if start - end + len(fill) > len(text):
        return text
    return extract_to_nearest_space(text, start) + fill + extract_to_nearest_space(text, end)


def get_formatted_sections(text: str) -> List[FormattedSection]:
    """
    Split the text by triple quotes. Return all sections and their labels.
    For example:
    text =
    '''
    Hello here is my code:
    ```python
    a = 2
    ```
    should return the following list:
    [
    (None, "\nHello here is my code:\n", True),
    ('python', "\na = 2\n", True),
    ]
    """
    sections = text.split('```')
    is_block = True
    labels_texts_complete = []
    for i, section in enumerate(sections):
        is_block = not is_block
        if section == '':
            continue
        if is_block:
            is_single_line = '\n' not in section
            text_in_quote_line = section.split('\n')[0].strip()
            if not is_single_line and ' ' not in text_in_quote_line:
                label = text_in_quote_line
                section = '\n' + '\n'.join(section.split('\n')[1:])
            else:
                label = ''
        else:
            label = None
        is_last = i == len(sections) - 1
        incomplete = is_last and is_block
        labels_texts_complete.append(FormattedSection(label, section, not incomplete))
    return labels_texts_complete


def convert_formatted_sections_to_text(formatted_sections: List[FormattedSection]) -> str:
    """
    Convert a LabelTextComplete to text.
    """
    text = ''
    for formatted_section in formatted_sections:
        label, section, is_complete = formatted_section.to_tuple()
        if label is not None:
            text += f'```{label}'
        text += section
        if label is not None and is_complete:
            text += '```'
    return text
