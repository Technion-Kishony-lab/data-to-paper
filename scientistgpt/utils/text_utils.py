import textwrap

import colorama


def format_str(s: str):
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


def print_red(text: str, message_callback=None):
    print(colorama.Fore.RED + text + colorama.Style.RESET_ALL)
    if message_callback:
        message_callback('Information', text)


def print_wrapped_text_with_code_blocks(text: str, text_color: str, code_color: str, width: int):

    def print_color(is_cd: bool):
        print(code_color if is_cd else text_color, end='')

    text = wrap_string(text, width=width)
    is_code = False
    print_color(is_code)
    for line in text.splitlines():
        if '```' in line:
            is_code = not is_code
            print_color(is_code)
        else:
            print(line)
    print(colorama.Style.RESET_ALL, end='')
