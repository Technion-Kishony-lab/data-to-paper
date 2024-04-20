import re
from typing import Optional, Dict, Tuple, Callable
from functools import partial

import colorama
from pygments.formatters.html import HtmlFormatter
from pygments.lexers import PythonLexer
from pygments.lexer import RegexLexer
from pygments.formatters import Terminal256Formatter
from pygments.lexers import TextLexer
from pygments.styles import get_style_by_name
from pygments import highlight, token

from .formatted_sections import FormattedSections
from .text_formatting import wrap_string
from data_to_paper.latex.latex_to_html import convert_latex_to_html
from ..env import CHOSEN_APP

COLORS_TO_LIGHT_COLORS = {
    colorama.Fore.BLACK: colorama.Fore.LIGHTBLACK_EX,
    colorama.Fore.RED: colorama.Fore.LIGHTRED_EX,
    colorama.Fore.GREEN: colorama.Fore.LIGHTGREEN_EX,
    colorama.Fore.YELLOW: colorama.Fore.LIGHTYELLOW_EX,
    colorama.Fore.BLUE: colorama.Fore.LIGHTBLUE_EX,
    colorama.Fore.MAGENTA: colorama.Fore.LIGHTMAGENTA_EX,
    colorama.Fore.CYAN: colorama.Fore.LIGHTCYAN_EX,
    colorama.Fore.WHITE: colorama.Fore.LIGHTWHITE_EX,
    "": "",
}

style = get_style_by_name("monokai")
terminal_formatter = Terminal256Formatter(style=style)
html_formatter = HtmlFormatter(style=style, cssclass='text_highlight')
html_textblock_formatter = HtmlFormatter(style=style, cssclass='textblock_highlight')

if CHOSEN_APP == 'pyside':
    html_code_formatter = HtmlFormatter(style=style)
else:
    html_code_formatter = HtmlFormatter(style=style, cssclass="code_highlight", prestyles="margin-left: 1.5em;")


class CSVLexer(RegexLexer):
    name = 'CSV'
    aliases = ['csv']
    filenames = ['*.csv']

    tokens = {
        'root': [
            (r'\b[0-9]+\b', token.Number.Integer),
            (r'\b[0-9]*\.[0-9]+\b', token.Number.Float),
            (r'0[oO]?[0-7]+', token.Number.Oct),  # Octal literals
            (r'0[xX][a-fA-F0-9]+', token.Number.Hex),  # Hexadecimal literals
            (r'\b[0-9]+[jJ]\b', token.Number),  # Complex numbers
            (r'.', token.Token.Name),
        ]
    }


def python_to_highlighted_html(code_str: str) -> str:
    return highlight(code_str, PythonLexer(), html_code_formatter)


def output_to_highlighted_html(output_str: str) -> str:
    return highlight(output_str, CSVLexer(), html_code_formatter)


def python_to_highlighted_text(code_str: str, color: str = '') -> str:
    if color:
        return highlight(code_str, PythonLexer(), terminal_formatter)
    else:
        return code_str


def md_to_html(md):
    """
    Convert markdown to html
    """
    # Convert headers
    md = re.sub(pattern=r'(?m)^#### (.*)', repl=r'<h4>\1</h4>', string=md)
    md = re.sub(pattern=r'(?m)^### (.*)', repl=r'<h3>\1</h3>', string=md)
    md = re.sub(pattern=r'(?m)^## (.*)', repl=r'<h2>\1</h2>', string=md)
    md = re.sub(pattern=r'(?m)^# (.*)', repl=r'<h1>\1</h1>', string=md)

    # Convert lists to bullets
    md = re.sub(pattern=r'(?m)^- (.*)', repl=r'<li>- \1</li>', string=md)

    # Convert bold and italic
    md = re.sub(pattern=r'\*\*(.*)\*\*', repl=r'<b>\1</b>', string=md)
    md = re.sub(pattern=r'\*(.*)\*', repl=r'<i>\1</i>', string=md)
    md = md.replace('\n\n', '<br>')
    return md


def text_to_html(text: str, textblock: bool = False, from_md: bool = False) -> str:
    if not textblock and CHOSEN_APP == 'pyside':
        if from_md:
            return md_to_html(text)
        return text.replace('\n', '<br>')

    # using some hacky stuff to get around pygments not highlighting text blocks, while kipping newlines as <br>
    text = '|' + text + '|'
    if textblock:
        html = highlight(text, TextLexer(), html_textblock_formatter)
    else:
        html = highlight(text, TextLexer(), html_formatter)
    html = html.replace('|', '', 1).replace('|', '', -1)
    return html.replace('\n', '<br>').replace('<br></pre>', '</pre>', -1)


def colored_text(text: str, color: str, is_color: bool = True) -> str:
    return color + text + colorama.Style.RESET_ALL if is_color and color != '' else text


def light_text(text: str, color: str, is_color: bool = True) -> str:
    return colored_text(text, COLORS_TO_LIGHT_COLORS[color], is_color)


def red_text(text: str, is_color: bool = True) -> str:
    return colored_text(text, colorama.Fore.RED, is_color)


def get_pre_html_format(text,
                        color: str = None,
                        font_style: str = 'normal',
                        font_size: int = 16,
                        font_weight: str = 'normal',
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


def identity(text: str) -> str:
    return text


REGULAR_FORMATTER = (colored_text, text_to_html)
BLOCK_FORMATTER = (light_text, partial(text_to_html, textblock=True))

TAGS_TO_FORMATTERS: Dict[Optional[str], Tuple[Callable, Callable]] = {
    False: REGULAR_FORMATTER,
    '': BLOCK_FORMATTER,
    True: BLOCK_FORMATTER,
    'text': REGULAR_FORMATTER,
    'markdown': REGULAR_FORMATTER,
    'md': REGULAR_FORMATTER,
    'python': (python_to_highlighted_text, python_to_highlighted_html),
    'output': (light_text, output_to_highlighted_html),
    'html': (colored_text, identity),
    'highlight': (colored_text, partial(get_pre_html_format, color='#334499', font_size=20, font_weight='bold',
                                        font_family="'Courier', sans-serif")),
    'comment': (colored_text, partial(get_pre_html_format, color='#424141', font_style='italic', font_size=16,
                                      font_weight='bold')),
    'system': (colored_text, partial(get_pre_html_format, color='#20191D', font_style='italic', font_size=16,
                                     font_family="'Courier', sans-serif")),
    'header': (light_text, partial(get_pre_html_format, color='#FF0000', font_size=12)),
    'latex': (colored_text, convert_latex_to_html),
}

NEEDS_NO_WRAPPING_FOR_NO_HTML = {'python', 'output', 'html', 'header'}
NEEDS_NO_WRAPPING_FOR_HTML = {'python', 'output', 'html', 'header', 'latex'}
POSSIBLE_MARKDOWN_LABELS = {'markdown', 'text', '', True, False}


def is_text_md(text: str) -> bool:
    return text.strip().startswith('#')


def format_text_with_code_blocks(text: str, text_color: str = '', from_md: Optional[bool] = None,
                                 width: Optional[int] = 150, is_html: bool = False) -> str:
    s = ''
    formatted_sections = FormattedSections.from_text(text)
    for formatted_section in formatted_sections:
        label, section, _, = formatted_section.to_tuple()
        formatter = TAGS_TO_FORMATTERS.get(label, BLOCK_FORMATTER)[is_html]
        is_section_md = \
            label == 'markdown' or label in POSSIBLE_MARKDOWN_LABELS and (from_md or from_md is None and is_text_md(section))
        if not is_html and label not in ['python', 'header', 'comment', 'system']:
            section = FormattedSections([formatted_section]).to_text()
        if is_html:
            if label not in NEEDS_NO_WRAPPING_FOR_HTML:
                section = wrap_string(section, width=width)
            if formatter == text_to_html:
                s += formatter(section, from_md=is_section_md)
            else:
                s += formatter(section)
        else:
            if label not in NEEDS_NO_WRAPPING_FOR_NO_HTML:
                section = wrap_string(section, width=width)
            s += formatter(section, text_color)
    return s
