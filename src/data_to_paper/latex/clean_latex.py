import re
from typing import Iterable

import regex

from .exceptions import UnwantedCommandsUsedInLatex

CHARS = {
    '&': r'\&',
    '%': r'\%',
    '#': r'\#',
    '_': r'\_',
    '$': r'\$',
    '~': r'\textasciitilde{}',
    '^': r'\textasciicircum{}',
    '<': r'$<$',
    '>': r'$>$',
    '≤': r'$\leq$',
    '≥': r'$\geq$',
    '≠': r'$\neq$',
    '±': r'$\pm$',
    '×': r'$\times$',
    '÷': r'$\div$',
    '°': r'$^{\circ}$',
    '∞': r'$\infty$',
    '√': r'$\sqrt{}$',
    '∑': r'$\sum$',
    '∏': r'$\prod$',
    '|': r'\textbar{}',
    '∈': r'$\in$',
    '∉': r'$\notin$',
    '∀': r'$\forall$',
    '∃': r'$\exists$',
    '∅': r'$\emptyset$',
    '\xe2': r'\^a',
    '\u200b': r'',  # zero width space
    '\u202f': r' ',  # narrow no-break space
}

NON_UTF8_CHARS = {
    '–': r'--',
    '’': r"",
    '≤': r'$\leq$',
    '≥': r'$\geq$',
    '±': r'+-',
    '²': r'$^2$',
    '³': r'$^3$',
    '¼': r'$\frac{1}{4}$',
    '½': r'$\frac{1}{2}$',
    '¾': r'$\frac{3}{4}$',
    '×': r'$\times$',
    '÷': r'$\div$',
    '°': r'$^{\circ}$',
    '∞': r'$\infty$',
    '√': r'$\sqrt{}$',
    '∑': r'$\sum$',
    '∏': r'$\prod$',
    '∈': r'$\in$',
    '∉': r'$\notin$',
    '∀': r'$\forall$',
    '∃': r'$\exists$',
    '∅': r'$\emptyset$',
    '∆': r'$\Delta$',
    '∇': r'$\nabla$',
    '∂': r'$\partial$',
    '“': r'"',
    '”': r'"',
}

assert all(len(c) == 1 for c in CHARS.keys())

MATH_PATTERN = r"""
(?<!\\)    # negative look-behind to make sure start is not escaped
(?:        # start non-capture group for all possible match starts
  # group 1, match dollar signs only
  # single or double dollar sign enforced by look-arounds
  ((?<!\$)\${1,2}(?!\$))|
  # group 2, match escaped parenthesis
  (\\\()|
  # group 3, match escaped bracket
  (\\\[)|
  # group 4,
  (\\begin\{(?:equation\*?|align\*?)\})|
  # group 5, match table and figure environments
  (\\begin\{(?:figure|lstlisting)\})|
  # group 6, match non-typesetting commands
  (\\(?:ref|label|autoref)\{)
)
# if group 1 was start
(?(1)
  # non greedy match everything in between
  # group 1 matches do not support recursion
  (.*?)(?<!\\)
  # match ending double or single dollar signs
  (?<!\$)\1(?!\$)|
# else
(?:
  # greedily and recursively match everything in between
  # groups 2, 3, 4, and 5 support recursion
  ((?:.|\n|\r)*?(?R)?(?:.|\n|\r)*?)(?<!\\)
  (?:
    # if group 2 was start, escaped parenthesis is end
    (?(2)\\\)|  
    # if group 3 was start, escaped bracket is end
    (?(3)\\\]|     
    # if group 4 was start, match end equation or end align
    (?(4)\\end\{(?:equation\*?|align\*?)\}| 
    # if group 5 was start, match end figure or end table
    (?(5)\\end\{(?:figure|lstlisting)\}|
    # else, match end of non-typesetting command
    \})
  )
)))))
"""

TABLES_CHARS = {
    r'>': r'$>$',
    r'<': r'$<$',
    r'=': r'$=$',
    r'|': r'\textbar{}',
}


def escape_special_chars_and_symbols_in_table(table: str,
                                              begin: str = r'\begin{tabular}',
                                              end: str = r'\end{tabular}') -> str:
    """
    Apply replace_special_chars to the tabular part of a latex table.
    """
    # extract the tabular part from the table using split
    if begin not in table:
        raise ValueError(f'The Table does not contain the begin command: {begin}')
    if end not in table:
        raise ValueError(f'The Table does not contain the end command: {end}')
    before_tabular, tabular_part = table.split(begin, 1)
    tabular_part, after_tabular = tabular_part.split(end, 1)
    tabular_part = process_latex_text_and_math(tabular_part, _process_table_part)
    return before_tabular + begin + tabular_part + end + after_tabular


def _process_table_part(tabular_part: str) -> str:
    pattern = re.compile(r'(%s)' % '|'.join(re.escape(key) for key in TABLES_CHARS.keys()))
    repl_func = lambda match: TABLES_CHARS[match.group(1)]
    return re.sub(pattern, repl_func, tabular_part)


def replace_special_latex_chars(text):
    chars = ''.join(CHARS.keys())
    pattern = fr'(?<!\\)([{chars}])'
    repl_func = lambda match: CHARS[match.group(1)]
    return re.sub(pattern, repl_func, text)


def replace_non_utf8_chars(text):
    chars = ''.join(NON_UTF8_CHARS.keys())
    pattern = fr'(?<!\\)([{chars}])'
    repl_func = lambda match: NON_UTF8_CHARS[match.group(1)]
    return re.sub(pattern, repl_func, text)


def process_inside_and_outside_command(latex, inside_func, outside_func):
    # Split the latex string into parts outside and within \caption{...}
    parts = re.split(pattern=r'(\\caption\{.*?\})', string=latex, flags=re.DOTALL)

    # Process each part using the appropriate function
    processed_parts = [outside_func(part) if not part.startswith(r'\caption') else r'\caption{' + inside_func(
        part[len(r'\caption{'):-1]) + '}' for part in parts]

    # Reassemble the parts
    processed_latex = ''.join(processed_parts)

    return processed_latex


def process_latex_text_and_math(text, process_text=replace_special_latex_chars, process_math=None):
    if process_math is None:
        process_math = lambda x: x

    result = []
    last_end = 0

    for match in regex.finditer(MATH_PATTERN, text, flags=regex.VERBOSE):
        non_math_part = text[last_end:match.start()]

        processed_part = process_text(non_math_part)
        result.append(processed_part)

        possibly_math_part = match.group()
        # find `\caption{...} parts in possibly_math_part and apply escaping on what's inside the curly braces
        # apply process_math on possibly_math_part without the `\caption{...}` and then add the processed caption

        processed_math_part = process_inside_and_outside_command(possibly_math_part, process_text, process_math)

        result.append(processed_math_part)

        last_end = match.end()

    # Process the remaining non-math part after the last match
    non_math_part = text[last_end:]
    processed_part = process_text(non_math_part)
    result.append(processed_part)

    return "".join(result)


def wrap_as_latex_code_output(paragraph):
    return "\\begin{codeoutput}\n" + paragraph + "\n\\end{codeoutput}"


def check_usage_of_un_allowed_commands(latex_content: str, unwanted_commands: Iterable[str]):
    unwanted_commands_used = [c for c in unwanted_commands if c in latex_content]
    if unwanted_commands_used:
        raise UnwantedCommandsUsedInLatex(unwanted_commands_used)
