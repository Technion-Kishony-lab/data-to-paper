import re
import textwrap
from typing import Optional, Union, Tuple, Dict

ArgsOrKwargs = Union[Tuple[str], Dict[str, str]]


def format_with_args_or_kwargs(text: str, args_or_kwargs: ArgsOrKwargs) -> str:
    """
    Return the text formatted with the given args or kwargs.
    """
    if isinstance(args_or_kwargs, tuple):
        return text.format(*args_or_kwargs)
    else:
        return text.format(**args_or_kwargs)


def dedent_triple_quote_str(s: str, remove_repeated_spaces: bool = True):
    """
    Format a triple-quote string to remove extra indentation and leading newline.
    """
    if s.startswith('\n'):
        s = s[1:]
    s = textwrap.dedent(s)
    if remove_repeated_spaces:
        s = re.sub(r' +', ' ', s)
    return s


def wrap_string(input_string, width: Optional[int] = 40, indent: int = 0, new_line_indent: bool = False):
    """
    Add linebreaks to wrap a long string.
    """
    # split input string into lines
    lines = input_string.split('\n')
    wrapped_lines = []

    # wrap each line individually
    for line in lines:
        if width is None:
            wrapped_line = line
        else:
            wrapped_line = textwrap.fill(line, width=width).replace('\n', '\n\t' if new_line_indent else '\n')
        wrapped_lines.append(wrapped_line)

    # join wrapped lines back together with preserved line breaks
    wrapped_string = "\n".join(wrapped_lines)

    # add indent to each line if specified
    if indent > 0:
        wrapped_string = textwrap.indent(wrapped_string, ' ' * indent)

    return wrapped_string


def wrap_python_code(code, width=70):
    wrapped_lines = []
    for line in code.split('\n'):
        stripped_line = line.strip()
        # Wrap comments
        if stripped_line.startswith("#"):
            # Preserve the leading whitespace
            leading_whitespace = line[:line.index("#")]
            wrapped_comment = textwrap.fill(stripped_line, width=width,
                                            initial_indent=leading_whitespace,
                                            subsequent_indent=leading_whitespace + "# ",
                                            break_long_words=False,
                                            break_on_hyphens=False)
            wrapped_lines.extend(wrapped_comment.split('\n'))
        # Wrap non-empty lines that are not comments
        elif stripped_line:
            wrapped_line = textwrap.wrap(line, width=width,
                                         break_long_words=False,
                                         break_on_hyphens=False)
            for i, part in enumerate(wrapped_line[:-1]):
                wrapped_lines.append(part + " \\")
            # Align the continuation lines with the original line's indentation
            continuation_indent = len(line) - len(line.lstrip())
            wrapped_lines.append(" " * continuation_indent + wrapped_line[-1])
        else:
            wrapped_lines.append(line)
    return "\n".join(wrapped_lines)


def format_str_by_direct_replace(text: str, replacements: dict):
    """
    Replace all occurrences of the keys in replacements with their corresponding values.
    """
    for key, value in replacements.items():
        text = text.replace('{' + key + '}', str(value))
    return text


def wrap_text_with_triple_quotes(text: str, header: str = '') -> str:
    """
    Wrap text with triple quotes.
    """
    return f'```{header}\n{text}\n```'


def forgiving_format(string, *args, **kwargs):
    """
    A forgiving version of str.format() that returns the original string if there are no matching arguments.
    """

    # Regular expression pattern to match placeholders in the string
    pattern = re.compile(r'\{\{.*?\}\}|\{.*?\}')  # {{var}} or {var}

    def substitute(match):
        nonlocal args
        match = match.group()
        if match[:2] == '{{' and match[-2:] == '}}':
            return match[1:-1]
        if match == '{}':
            if len(args) > 0:
                replace_with = str(args[0])
                args = args[1:]
            else:
                replace_with = '{}'
        else:
            key = match[1:-1]
            if key in kwargs:
                replace_with = str(kwargs[key])
            else:
                replace_with = match
        return replace_with

    return re.sub(pattern, substitute, string)
