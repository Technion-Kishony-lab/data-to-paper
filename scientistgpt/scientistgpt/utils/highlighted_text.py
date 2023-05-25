from typing import Optional, Dict, Tuple, Callable

import colorama
from pygments.formatters.html import HtmlFormatter
from pygments.lexers import PythonLexer
from pygments.formatters import Terminal256Formatter
from pygments.lexers import TextLexer
from pygments.styles import get_style_by_name
from pygments import highlight

from .formatted_sections import FormattedSections
from .text_formatting import wrap_string

style = get_style_by_name("monokai")
terminal_formatter = Terminal256Formatter(style=style)
html_formatter = HtmlFormatter(style=style, cssclass='text_highlight')
html_textblock_formatter = HtmlFormatter(style=style, cssclass='textblock_highlight')
html_code_formatter = HtmlFormatter(style=style, cssclass="code_highlight", prestyles="margin-left: 1.5em;")


def highlight_python_code(code_str: str, is_html: bool = False, *args) -> str:
    if is_html:
        return highlight(code_str, PythonLexer(), html_code_formatter)
    else:
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


def colored_text(text: str, color: str, is_color: bool = True) -> str:
    return color + text + colorama.Style.RESET_ALL if is_color else text


def red_text(text: str, is_color: bool = True) -> str:
    return colored_text(text, colorama.Fore.RED, is_color)


def print_red(text: str, **kwargs):
    print(colored_text(text, colorama.Fore.RED), **kwargs)


def _get_pre_html_format(text, color, font_style: str = 'normal', font_size: int = 16, font_weight: str = 'normal',
                         font_family: str = None):
    s = '<pre style="'
    if color:
        s += f'color: {color};'
    if font_style:
        s += f'font-style: {font_style};'
    if font_size:
        s += f'font-size: {font_size}px;'
    if font_weight:
        s += f'font-weight: {font_weight};'
    if font_family:
        s += f'font-family: {font_family};'
    s += '">'
    return s + text + '</pre>'


def format_system(text: str, is_html: bool = False, text_color: str = '', block_color: str = '') -> str:
    if is_html:
        return _get_pre_html_format(text, color='#20191D', font_style='italic', font_size=16,
                                    font_family="'Courier', sans-serif")
    else:
        return colored_text(text, text_color)


def format_comment(text: str, is_html: bool = False, text_color: str = '', block_color: str = '') -> str:
    if is_html:
        text = text.strip()
        return _get_pre_html_format(text, color='#424141', font_style='italic', font_size=16, font_weight='bold')
    else:
        return colored_text(text, text_color)


def format_highlight(text: str, is_html: bool = False, text_color: str = '', block_color: str = '') -> str:
    if is_html:
        return _get_pre_html_format(text, color='#334499', font_size=20, font_weight='bold',
                                    font_family="'Courier', sans-serif")
    else:
        return colored_text(text, text_color)


def format_header(text: str, is_html: bool = False, text_color: str = '', block_color: str = '') -> str:
    if is_html:
        return _get_pre_html_format(text, color='#FF0000', font_size=12)
    else:
        return colored_text(text, block_color)


def format_normal_text(text: str, is_html: bool = False, text_color: str = '', block_color: str = '') -> str:
    if is_html:
        return text_to_html(text)
    else:
        return colored_text(text, text_color)


def format_text_block(text: str, is_html: bool = False, text_color: str = '', block_color: str = '') -> str:
    if is_html:
        return text_to_html(text, textblock=True)
    else:
        return colored_text(text, block_color)


REGULAR_FORMATTER = (format_normal_text, True)
BLOCK_FORMATTER = (format_text_block, True)

TAGS_TO_FORMATTERS: Dict[Optional[str], Tuple[Callable, bool]] = {
    None: REGULAR_FORMATTER,
    '': BLOCK_FORMATTER,
    'text': REGULAR_FORMATTER,
    'python': (highlight_python_code, False),
    'highlight': (format_highlight, True),
    'comment': (format_comment, True),
    'system': (format_system, True),
    'header': (format_header, True),
}


def format_text_with_code_blocks(text: str, text_color: str = '', block_color: str = '',
                                 width: int = 80, is_html: bool = False) -> str:
    s = ''
    formatted_sections = FormattedSections.from_text(text)
    for formatted_section in formatted_sections:
        label, section = formatted_section.to_tuple()
        formatter, should_wrap = TAGS_TO_FORMATTERS.get(label, BLOCK_FORMATTER)
        if should_wrap:
            section = wrap_string(section, width=width)
        s += formatter(section, is_html, text_color, block_color)
    return s
