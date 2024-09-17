import re
from typing import Optional, Dict, Tuple, Callable
from functools import partial

import colorama
from pygments.formatters.html import HtmlFormatter
from pygments.lexers import PythonLexer, JsonLexer
from pygments.lexer import RegexLexer
from pygments.formatters import Terminal256Formatter
from pygments.styles import get_style_by_name
from pygments import highlight, token
from typing import List

from data_to_paper.latex.latex_to_html import convert_latex_to_html
from data_to_paper.env import CHOSEN_APP

from .formatted_sections import FormattedSections
from .text_formatting import wrap_string, wrap_as_block

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
            # Matches integers, floats, and numbers in scientific notation with optional leading +/-
            (r'[-+]?\b[0-9]+(\.[0-9]*)?([eE][-+]?[0-9]+)?\b', token.Number.Float),
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


def python_to_highlighted_text(code_str: str, color: str = '', label: Optional[str] = None) -> str:
    if color:
        return highlight(code_str, PythonLexer(), terminal_formatter)
    else:
        return code_str


def json_to_highlighted_html(json_str: str) -> str:
    return highlight(json_str, JsonLexer(), html_code_formatter)


def json_to_highlighted_text(json_str: str, color: str = '', label: Optional[str] = None) -> str:
    if color:
        return highlight(json_str, JsonLexer(), terminal_formatter)
    else:
        return json_str


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
        # TODO: The bullet formatting looks ugly. Disable it for now.
        # elif line.startswith('- '):
        #     html_line = f'<li>- {line[2:]}</li>'
        # elif line.startswith('* '):
        #     html_line = f'<li>* {line[2:]}</li>'
        elif not line.strip():
            html_line = '<br>'
        else:
            html_line = line + '<br>'
        html_lines.append(html_line)
    md = '\n'.join(html_lines)

    # Convert bold:
    md = re.sub(pattern=r'\*\*(.*?)\*\*', repl=r'<b>\1</b>', string=md)

    # Convert italics:
    md = re.sub(pattern=r'\*(.*?)\*', repl=r'<i>\1</i>', string=md)

    # Convert code, flanked by backticks:
    md = re.sub(pattern=r'`([^`]+)`', repl=r'<span class="codeline">\1</span>', string=md)
    return md


def text_to_html(text: str, label: Optional[str] = None,
                 from_md: bool = False, css_class: Optional[str] = 'markdown') -> str:
    # strip newlines from the right end of the text:
    text = text.strip('\n')
    text = _escape_html(text)
    if from_md:
        html = md_to_html(text)
    else:
        html = text.replace('\n', '<br>')
    if css_class is not None:
        html = f'<div class="{css_class}">{html}</div>'
    return html


def colored_text(text: str, color: str, is_color: bool = True, is_light: bool = False) -> str:
    if not is_color or color == '':
        return text
    if is_light:
        color = COLORS_TO_LIGHT_COLORS[color]
    return color + text + colorama.Style.RESET_ALL


def red_text(text: str, is_color: bool = True) -> str:
    return colored_text(text, colorama.Fore.RED, is_color)


def _colored_block(text: str, label: Optional[str], color: str, with_tags: bool = True,
                   is_color: bool = True, is_light: bool = False) -> str:
    if with_tags and label:
        text = wrap_as_block(text, label)
    return colored_text(text, color, is_color, is_light)


_light_colored_block = partial(_colored_block, is_light=True)
_light_colored_block_no_tags = partial(_light_colored_block, with_tags=False)


def _escape_html(text: str) -> str:
    return text.replace('<', '&lt;').replace('>', '&gt;')


def get_pre_html_format(text,
                        color: str = None,
                        font_style: str = None,  # normal, italic, oblique
                        font_size: int = None,
                        font_weight: str = None,  # normal, bold
                        font_family: str = None):
    text = _escape_html(text)
    s = '<pre style="white-space: pre-wrap;'
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


def _block_to_html(text: str, label: Optional[str], with_tags: bool = True, **kwargs) -> str:
    if with_tags and label is not None:
        text = wrap_as_block(text, label)
    return text_to_html(text, css_class='tripled_quote')


def identity(text) -> str:
    return text


NORMAL_FORMATTERS = (_colored_block, text_to_html)
BLOCK_FORMATTERS = (_light_colored_block, _block_to_html)

TAGS_TO_FORMATTERS: Dict[Optional[str], Tuple[Callable, Callable]] = {
    None: NORMAL_FORMATTERS,
    '': BLOCK_FORMATTERS,
    'markdown': (_light_colored_block, partial(text_to_html, from_md=True, label=None)),
    'md': (_light_colored_block, partial(text_to_html, from_md=True, label=None)),
    'python': (python_to_highlighted_text, python_to_highlighted_html),
    'output': (_light_colored_block, output_to_highlighted_html),
    'html': (_light_colored_block, identity),
    'header': (_light_colored_block_no_tags, partial(get_pre_html_format, color='#FF0000', font_size=12)),
    'latex': (_light_colored_block, convert_latex_to_html),
    'error': (partial(_light_colored_block_no_tags, color=colorama.Fore.RED),
              partial(text_to_html, css_class="runtime_error")),
    'json': (json_to_highlighted_text, json_to_highlighted_html),
    'system': (_light_colored_block_no_tags, NotImplemented),
    'comment': (_light_colored_block_no_tags, NotImplemented),
}


def is_text_md(text: str) -> bool:
    return text.strip().startswith('#')


def format_text_with_code_blocks(text: str, text_color: str = '', from_md: Optional[bool] = None,
                                 width: Optional[int] = 150, is_html: bool = False,
                                 do_not_format: List[str] = None) -> str:
    if from_md is None:
        from_md = is_text_md(text)
    do_not_format = do_not_format or []
    s = ''
    formatted_sections = FormattedSections.from_text(text)
    for formatted_section in formatted_sections:
        label, section, is_complete = formatted_section.to_tuple()
        if label is not None:
            label = label.lower()
        if not is_complete:
            formatters = NORMAL_FORMATTERS
            section = formatted_section.to_text()
        else:
            if label in do_not_format:
                formatters = BLOCK_FORMATTERS
            else:
                formatters = TAGS_TO_FORMATTERS.get(label, BLOCK_FORMATTERS)
        formatter = formatters[is_html]
        if is_html:
            if formatter == text_to_html:
                s += formatter(section, from_md=from_md)
            elif formatter == _block_to_html:
                s += formatter(section, label=label)
            else:
                s += formatter(section)
        else:
            section = wrap_string(section, width=width)
            s += formatter(section, color=text_color, label=label)
    return s
