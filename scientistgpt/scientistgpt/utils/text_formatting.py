import re
import textwrap
from typing import Optional


def dedent_triple_quote_str(s: str, remove_repeated_spaces: bool = True):
    """
    Format a triple-quote string to remove extra indentation and leading newline.
    """
    s = textwrap.dedent(s).lstrip()
    if remove_repeated_spaces:
        s = re.sub(r' +', ' ', s)
    return s


def wrap_string(input_string, width: Optional[int] = 40, indent=0):
    """
    Add linebreaks to wrap a long string.
    """
    # split input string into lines
    lines = input_string.splitlines()
    wrapped_lines = []

    # wrap each line individually
    for line in lines:
        if width is None:
            wrapped_line = line
        else:
            wrapped_line = textwrap.fill(line, width=width)
        wrapped_lines.append(wrapped_line)

    # join wrapped lines back together with preserved line breaks
    wrapped_string = "\n".join(wrapped_lines)

    # add indent to each line if specified
    if indent > 0:
        wrapped_string = textwrap.indent(wrapped_string, ' ' * indent)

    return wrapped_string


def format_str_by_direct_replace(text: str, replacements: dict):
    """
    Replace all occurrences of the keys in replacements with their corresponding values.
    """
    for key, value in replacements.items():
        text = text.replace('{' + key + '}', str(value))
    return text
