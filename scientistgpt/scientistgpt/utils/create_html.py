import colorama
from pygments.formatters.html import HtmlFormatter
from pygments.lexers import PythonLexer
from pygments.formatters import Terminal256Formatter
from pygments.lexers import TextLexer
from pygments.styles import get_style_by_name
from pygments import highlight

from .text_formatting import wrap_string

style = get_style_by_name("monokai")
terminal_formatter = Terminal256Formatter(style=style)
html_formatter = HtmlFormatter(style=style, cssclass='text_highlight')
html_textblock_formatter = HtmlFormatter(style=style, cssclass='textblock_highlight')
html_code_formatter = HtmlFormatter(style=style, cssclass="code_highlight", prestyles="margin-left: 1.5em;")


def highlight_python_code(code_str: str, is_html: bool = False) -> str:
    if is_html:
        return highlight(code_str, PythonLexer(), html_code_formatter)
    return highlight(code_str, PythonLexer(), terminal_formatter)


def text_to_html(text: str, textblock: bool = False) -> str:

    # using some hacky stuff to get around pygments not highlighting text blocks, while kipping newlines as <br>
    text = '|' + text + '|'
    if textblock:
        html = highlight(text, TextLexer(), html_textblock_formatter)
    else:
        html = highlight(text, TextLexer(), html_formatter)
    html = html.replace('|', '', 1).replace('|', '', -1)

    return html.replace('\n', '<br>').replace('<br></pre>', '</pre>', -1)


def highlight_html(text):
    font_family = "font-family: 'Courier', sans-serif;"
    return f'<pre style="color: #334499; font-weight: bold; font-size: 20px; {font_family}">{text}</pre>'


def colored_text(text: str, color: str, is_color: bool = True) -> str:
    return color + text + colorama.Style.RESET_ALL if is_color else text


def red_text(text: str, is_color: bool = True) -> str:
    return colored_text(text, colorama.Fore.RED, is_color)


def print_red(text: str, **kwargs):
    print(colored_text(text, colorama.Fore.RED), **kwargs)


def print_magenta(text: str, **kwargs):
    print(colored_text(text, colorama.Fore.MAGENTA), **kwargs)


def format_text_with_code_blocks(text: str, text_color: str = '', block_color: str = '',
                                 width: int = 80, is_html: bool = False, is_comment=False, is_system=False) -> str:
    text = text.strip()
    if is_comment:
        return f'<pre style="color: #424141; font-weight: bold; font-style: italic; font-size: 16px;">{text}</pre>'
    elif is_system:
        font_family = "font-family: 'Courier', sans-serif;"
        return f'<pre style="color: #20191D; font-style: italic; font-size: 16px;' \
               f'{font_family}">{wrap_string(text, width=width)}</pre>'
    sections = text.split("```")
    s = ''
    in_text_block = True
    for section in sections:
        if in_text_block:
            if is_html:
                s += text_to_html(wrap_string(section, width=width))
            else:
                s += text_color + wrap_string(section, width=width) + colorama.Style.RESET_ALL + '\n'
        else:
            if section.startswith('python'):
                # remove the first line of the language name
                section = '\n'.join(section.splitlines()[1:])
                s += highlight_python_code(section, is_html)
            elif section.startswith('highlight'):
                # remove the first line of the language name
                section = '\n'.join(section.splitlines()[1:])
                s += highlight_html(wrap_string(section, width=width))
            else:
                if is_html:
                    s += text_to_html(wrap_string(section, width=width), textblock=True)
                else:
                    s += block_color + wrap_string(section, width=width) + colorama.Style.RESET_ALL
        in_text_block = not in_text_block
    return s



