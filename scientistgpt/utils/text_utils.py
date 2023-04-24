import textwrap
import re
from typing import Optional, Tuple, Union

import colorama

from pygments.lexers import PythonLexer
from pygments.formatters import Terminal256Formatter
from pygments.styles import get_style_by_name
from pygments import highlight


style = get_style_by_name("monokai")
python_formatter = Terminal256Formatter(style=style)


def highlight_python_code(code_str: str):
    return highlight(code_str, PythonLexer(), python_formatter)


def dedent_triple_quote_str(s: str):
    """
    Format a triple-quote string to remove extra indentation and leading newline.
    """
    return textwrap.dedent(s).lstrip()


def wrap_string(input_string, width=40, indent=0):
    """
    Add linebreaks to wrap a long string.
    """
    # split input string into lines
    lines = input_string.splitlines()
    wrapped_lines = []

    # wrap each line individually
    for line in lines:
        wrapped_line = textwrap.fill(line, width=width)
        wrapped_lines.append(wrapped_line)

    # join wrapped lines back together with preserved line breaks
    wrapped_string = "\n".join(wrapped_lines)

    # add indent to each line if specified
    if indent > 0:
        wrapped_string = textwrap.indent(wrapped_string, ' ' * indent)

    return wrapped_string


def colored_text(text: str, color: str, is_color: bool = True) -> str:
    return color + text + colorama.Style.RESET_ALL if is_color else text


def red_text(text: str, is_color: bool = True) -> str:
    return colored_text(text, colorama.Fore.RED, is_color)


def print_red(text: str, **kwargs):
    print(colored_text(text, colorama.Fore.RED), **kwargs)


def print_magenta(text: str, **kwargs):
    print(colored_text(text, colorama.Fore.MAGENTA), **kwargs)


def format_text_with_code_blocks(text: str, text_color: str, code_color: str, width: int,
                                 is_python: bool = True) -> str:

    sections = text.split("```")
    s = ''
    in_text_block = True
    for section in sections:
        if in_text_block:
            s += text_color + wrap_string(section, width=width) + colorama.Style.RESET_ALL + '\n'
        else:
            if is_python:
                highlighted_code = highlight_python_code(section)
                # check if the first line is the language name
                if 'python' in highlighted_code.splitlines()[0].lower():
                    highlighted_code = '\n'.join(highlighted_code.splitlines()[1:])
                s += highlighted_code
            else:
                s += code_color + section + colorama.Style.RESET_ALL
        in_text_block = not in_text_block
    return s


def word_count(text: str) -> int:
    """
    Count the number of words in provided test.
    """
    return len(re.findall(r'\w+', text))


def line_count(text: str) -> int:
    """
    Count the number of lines in provided test.
    """
    return len(text.splitlines())


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
        if not left_bracket in optional_brackets.keys() or right_bracket != optional_brackets[left_bracket]:
            # just find the first instance of the right tag and return the text between the left tag and the right tag
            start = text.find(left_tag)
            if start == -1:
                raise ValueError(f'Could not find left tag {left_tag} in text')
            end = text.find(right_tag, start)
            if end == -1:
                raise ValueError(f'Could not find left tag {right_tag} in text')
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

def extract_text_between_brackets(text: str, open_bracket: str):
    """
    use stack to find matching closing bracket for the first open bracket, use stack to find matching closing bracket.
    return the text between the first open bracket and the matching closing bracket without the brackets.
    :param text:
    :param open_bracket:
    :return:
    """
    start = text.find(open_bracket)
    if start == -1:
        raise ValueError(f'Could not find open bracket {open_bracket} in text')
    end = start + 1
    stack = [open_bracket]
    while len(stack) > 0:
        if text[end] == open_bracket:
            stack.append(open_bracket)
        elif text[end] == ']' and open_bracket == '[':
            stack.pop()
        elif text[end] == '}' and open_bracket == '{':
            stack.pop()
        elif text[end] == ')' and open_bracket == '(':
            stack.pop()
        end += 1
    return text[start + 1:end - 1]


def concat_words_with_commas_and_and(words: list, wrap_with: Optional[Union[str, Tuple[str, str]]] = None):
    """
    Concatenate a list of words with commas and an 'and' at the end.

    wrap_with: if str: wrap each word with the provided string. if tuple: wrap each word with the first string
    on the left and the second string on the right.
    """
    if isinstance(wrap_with, str):
        words = [wrap_with + word + wrap_with for word in words]
    elif isinstance(wrap_with, tuple):
        words = [wrap_with[0] + word + wrap_with[1] for word in words]
    elif wrap_with is not None:
        raise ValueError(f'wrap_with must be either str or tuple, not {type(wrap_with)}')
    if len(words) == 0:
        return ''
    if len(words) == 1:
        return words[0]
    if len(words) == 2:
        return words[0] + ' and ' + words[1]
    return ', '.join(words[:-1]) + ', and ' + words[-1]
