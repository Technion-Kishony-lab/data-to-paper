import textwrap
import re
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
    If the right tag is None, then extract text from the left tag to the end of the text.
    """
    if left_tag not in text:
        raise ValueError('left tag missing')

    extracted = text.split(left_tag)[1]

    if right_tag is not None:
        if right_tag not in extracted:
            raise ValueError('right tag missing')
        extracted = extracted.split(right_tag)[0]

    if leave_tags:
        if right_tag is None:
            extracted = left_tag + extracted
        else:
            extracted = left_tag + extracted + right_tag

    return extracted


def concat_words_with_commas_and_and(words: list):
    """
    Concatenate a list of words with commas and an 'and' at the end.
    """
    if len(words) == 0:
        return ''
    if len(words) == 1:
        return words[0]
    if len(words) == 2:
        return words[0] + ' and ' + words[1]
    return ', '.join(words[:-1]) + ', and ' + words[-1]
