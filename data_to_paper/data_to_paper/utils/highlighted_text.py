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
from typing import List

from data_to_paper.latex.latex_to_html import convert_latex_to_html
from data_to_paper.env import CHOSEN_APP

from .formatted_sections import FormattedSections
from .text_formatting import wrap_string

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


def demote_html_headers(html, demote_by=1):
    """
    Demote HTML header tags by a specified number of levels.
    """
    if demote_by < 1:
        return html  # Return the original html if demote_by is less than 1

    # Function to replace header tags
    def replace_tag(match):
        current_level = int(match.group(1))
        new_level = min(current_level + demote_by, 6)  # HTML only supports headers up to <h6>
        return f'<h{new_level}>{match.group(2)}</h{new_level}>'

    # Regex to find headers and replace
    return re.sub(pattern=r'<h([1-6])>(.*?)</h\1>', repl=replace_tag, string=html)


def md_to_html(md):
    """
    Convert markdown to HTML while managing newline characters appropriately after headers.
    """
    html_lines = []
    for line in md.split('\n'):
        if re.match(pattern=r'^#{1,5} ', string=line):
            header_level = len(line.split(' ')[0])
            html_line = f'<h{header_level}>{line[header_level + 1:]}</h{header_level}>'
            if html_lines and html_lines[-1] == '<br>':
                html_lines.pop()
        elif line.startswith('- '):
            html_line = f'<li>- {line[2:]}</li>'
        elif line.startswith('* '):
            html_line = f'<li>* {line[2:]}</li>'
        elif not line.strip():
            html_line = '<br>'
        else:
            html_line = line + '<br>'
        html_lines.append(html_line)
    md = '\n'.join(html_lines)

    # Convert bold and italic
    md = re.sub(pattern=r'\*\*(.*?)\*\*', repl=r'<b>\1</b>', string=md)
    md = re.sub(pattern=r'\*(.*?)\*', repl=r'<i>\1</i>', string=md)
    return md


def text_to_html(text: str, from_md: bool = False, css_class: str = 'markdown') -> str:
    # strip newlines from the right end of the text:
    while text and text[-1] == '\n':
        text = text[:-1]
    text = text.replace('<', '&lt;').replace('>', '&gt;')
    if from_md:
        html = md_to_html(text)
    else:
        html = text.replace('\n', '<br>')
    return f'<div class="{css_class}">{html}</div>'


def colored_text(text: str, color: str, is_color: bool = True) -> str:
    return color + text + colorama.Style.RESET_ALL if is_color and color != '' else text


def light_text(text: str, color: str, is_color: bool = True) -> str:
    return colored_text(text, COLORS_TO_LIGHT_COLORS[color], is_color)


def red_text(text: str, is_color: bool = True) -> str:
    return colored_text(text, colorama.Fore.RED, is_color)


def green_text(text: str, is_color: bool = True) -> str:
    return colored_text(text, colorama.Fore.GREEN, is_color)


def get_pre_html_format(text,
                        color: str = None,
                        font_style: str = None,  # normal, italic, oblique
                        font_size: int = 16,
                        font_weight: str = None,  # normal, bold
                        font_family: str = None):
    if color is None and font_style is None and font_size == 16 and font_weight is None and font_family is None:
        return f'<pre>{text}</pre>'
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
BLOCK_FORMATTER = (light_text, get_pre_html_format)

TAGS_TO_FORMATTERS: Dict[Optional[str], Tuple[Callable, Callable]] = {
    None: REGULAR_FORMATTER,
    '': BLOCK_FORMATTER,
    'text': REGULAR_FORMATTER,
    'markdown': REGULAR_FORMATTER,
    'md': REGULAR_FORMATTER,
    'python': (python_to_highlighted_text, python_to_highlighted_html),
    'output': (light_text, output_to_highlighted_html),
    'html': (colored_text, identity),
    'header': (light_text, partial(get_pre_html_format, color='#FF0000', font_size=12)),
    'latex': (colored_text, convert_latex_to_html),
    'error': (red_text, partial(text_to_html, css_class="runtime_error"))
}

NEEDS_NO_WRAPPING_FOR_NO_HTML = {'python', 'output', 'html', 'header'}
NEEDS_NO_WRAPPING_FOR_HTML = {'python', 'output', 'html', 'header', 'latex'}
POSSIBLE_MARKDOWN_LABELS = {'markdown', 'text', '', None}


def is_text_md(text: str) -> bool:
    return text.strip().startswith('#')


def format_text_with_code_blocks(text: str, text_color: str = '', from_md: Optional[bool] = None,
                                 width: Optional[int] = 150, is_html: bool = False,
                                 do_not_format: List[str] = None) -> str:
    do_not_format = do_not_format or []
    s = ''
    formatted_sections = FormattedSections.from_text(text)
    for formatted_section in formatted_sections:
        label, section, _, = formatted_section.to_tuple()
        is_section_md = (label == 'markdown' or label in POSSIBLE_MARKDOWN_LABELS
                         and (from_md or from_md is None and is_text_md(section)))
        if label in do_not_format and is_html:
            section = f'```{label}' + section + '```'
            label = ''
        formatter = TAGS_TO_FORMATTERS.get(label, BLOCK_FORMATTER)[is_html]
        if is_html:
            if formatter == text_to_html:
                s += formatter(section, from_md=is_section_md)
            else:
                s += formatter(section)
        else:
            if label not in ['python', 'header', 'comment', 'system']:
                section = FormattedSections([formatted_section]).to_text()
            section = wrap_string(section, width=width)
            s += formatter(section, text_color)
    return s
