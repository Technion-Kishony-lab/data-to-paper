import textwrap
import re
from typing import Tuple, Union

import colorama

from pygments.lexers import PythonLexer
from pygments.formatters import Terminal256Formatter
from pygments.styles import get_style_by_name
from pygments import highlight

style = get_style_by_name("monokai")
python_formatter = Terminal256Formatter(style=style)


def highlight_python_code(code_str: str):
    return highlight(code_str, PythonLexer(), python_formatter)


def dedent_triple_quote_str(s: str, remove_repeated_spaces: bool = True):
    """
    Format a triple-quote string to remove extra indentation and leading newline.
    """
    s = textwrap.dedent(s).lstrip()
    if remove_repeated_spaces:
        s = re.sub(r' +', ' ', s)
    return s


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


def format_text_with_code_blocks(text: str, text_color: str, block_color: str, width: int) -> str:
    sections = text.split("```")
    s = ''
    in_text_block = True
    for section in sections:
        if in_text_block:
            s += text_color + wrap_string(section, width=width) + colorama.Style.RESET_ALL + '\n'
        else:
            if section.startswith('python'):
                highlighted_code = highlight_python_code(section)
                # check if the first line is the language name
                if 'python' in highlighted_code.splitlines()[0].lower():
                    highlighted_code = '\n'.join(highlighted_code.splitlines()[1:])
                s += highlighted_code
            else:
                s += block_color + wrap_string(section, width=width) + colorama.Style.RESET_ALL
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


FROM_OPEN_BRACKET_TO_CLOSE_BRACKET = {'[': ']', '{': '}', '(': ')'}


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
        if text[end] == open_bracket:
            stack.append(open_bracket)
        elif text[end] == FROM_OPEN_BRACKET_TO_CLOSE_BRACKET[open_bracket]:
            stack.pop()
        end += 1
    if leave_brackets:
        return text[start:end]
    return text[start + 1:end - 1]


StrOrTupleStr = Union[str, Tuple[str, str]]


def nicely_join(words: list, wrap_with: StrOrTupleStr = '',
                prefix: StrOrTupleStr = '', suffix: StrOrTupleStr = '',
                separator: str = ', ', last_separator: str = ' and '):
    """
    Concatenate a list of words with commas and an 'and' at the end.

    wrap_with: if str: wrap each word with the provided string. if tuple: wrap each word with the first string
    on the left and the second string on the right.

    prefix: if str: add the provided string before the concatenated words. if tuple the first string is for singular
    and the second string is for plural.

    suffix: if str: add the provided string after the concatenated words. if tuple the first string is for singular
    and the second string is for plural.
    """

    def format_noun(noun: StrOrTupleStr, num: int):
        if isinstance(noun, str):
            pass
        elif isinstance(noun, tuple):
            if num_words == 1:
                noun = noun[0]
            else:
                noun = noun[1]
        else:
            raise ValueError(f'prefix must be either str or tuple, not {type(prefix)}')
        if '{}' in noun:
            noun = noun.format(num)
        if '[s]' in noun:
            noun = noun.replace('[s]', 's' if num_words > 1 else '')
        return noun

    # wrap each word with the provided string:
    if isinstance(wrap_with, str):
        words = [wrap_with + word + wrap_with for word in words]
    elif isinstance(wrap_with, tuple):
        words = [wrap_with[0] + word + wrap_with[1] for word in words]
    elif wrap_with is not None:
        raise ValueError(f'wrap_with must be either str or tuple, not {type(wrap_with)}')

    num_words = len(words)

    # concatenate the words:
    if num_words == 0:
        s = ''
    elif num_words == 1:
        s = words[0]
    elif num_words == 2:
        s = words[0] + last_separator + words[1]
    else:
        s = separator.join(words[:-1]) + last_separator + words[-1]

    return format_noun(prefix, num_words) + s + format_noun(suffix, num_words)


class NiceList(list):
    """
    A list that can be printed nicely.
    """
    def __init__(self, *args, wrap_with: StrOrTupleStr = '', prefix: StrOrTupleStr = '',
                 suffix: StrOrTupleStr = '', separator: str = ', ', last_separator: str = ' and '):
        super().__init__(*args)
        self.wrap_with = wrap_with
        self.prefix = prefix
        self.suffix = suffix
        self.separator = separator
        self.last_separator = last_separator

    def __str__(self):
        return nicely_join(self, self.wrap_with, self.prefix, self.suffix, self.separator, self.last_separator)

    def __repr__(self):
        return str(self)
