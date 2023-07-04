import os
import re
import shutil
import subprocess
import regex

from typing import Set, Optional, List

from data_to_paper.servers.types import Citation
from data_to_paper.utils.file_utils import run_in_temp_directory
from data_to_paper.utils.citataion_utils import get_non_latex_citations
from data_to_paper.utils.text_formatting import wrap_string

from .exceptions import LatexCompilationError, UnwantedCommandsUsedInLatex, TooWideTableOrText, NonLatexCitations

THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))

BIB_FILENAME: str = 'citations.bib'

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
    '|': r'\textbar{}',
}

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
  (\\begin\{(?:figure|table|lstlisting)\})|
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
    (?(5)\\end\{(?:figure|table|lstlisting)\}|
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
                                              begin: str = r'\begin{tabular}', end: str = r'\end{tabular}') -> str:
    # extract the tabular part from the table using split
    if begin not in table:
        raise ValueError(f'The Table does not contain the begin command: {begin}')
    if end not in table:
        raise ValueError(f'The Table does not contain the end command: {end}')
    before_tabular, tabular_part = table.split(begin, 1)
    tabular_part, after_tabular = tabular_part.split(end, 1)
    tabular_part = replace_special_chars(tabular_part, process_table_part)
    return before_tabular + begin + tabular_part + end + after_tabular


def process_table_part(tabular_part: str) -> str:
    pattern = re.compile(r'(%s)' % '|'.join(re.escape(key) for key in TABLES_CHARS.keys()))
    repl_func = lambda match: TABLES_CHARS[match.group(1)]
    return re.sub(pattern, repl_func, tabular_part)


def process_non_math_part(text):
    assert all(len(c) == 1 for c in CHARS.keys())
    text = text.encode('ascii', 'ignore').decode('utf-8')
    chars = ''.join(CHARS.keys())
    pattern = fr'(?<!\\)([{chars}])'
    repl_func = lambda match: CHARS[match.group(1)]
    return re.sub(pattern, repl_func, text)


def process_bibtex_id(bibtex_id: str) -> str:
    # "{}(),\\\"-#~^:'`ʹ";  # characters that are not allowed in bibtex ids and should be replaced with ' '
    # replace non unicode characters with their unicode equivalent
    bibtex_id = bibtex_id.encode('ascii', 'ignore').decode('utf-8')
    return re.sub(r'[{}(),\\\"-#~^:\'`ʹ]', ' ', bibtex_id)


def replace_special_chars(text, processing_func=process_non_math_part):
    result = []
    last_end = 0

    for match in regex.finditer(MATH_PATTERN, text, flags=regex.VERBOSE):
        non_math_part = text[last_end:match.start()]

        processed_part = processing_func(non_math_part)
        result.append(processed_part)

        possibly_math_part = match.group()
        # find `\caption{...} parts in possibly_math_part and apply escaping on what's inside the curly braces
        math_part = regex.sub(r'\\caption\{.*?\}',
                              lambda m: m.group().replace(m.group(0)[9:-1], processing_func(m.group(0)[9:-1])),
                              possibly_math_part)
        result.append(math_part)

        last_end = match.end()

    # Process the remaining non-math part after the last match
    non_math_part = text[last_end:]
    processed_part = processing_func(non_math_part)
    result.append(processed_part)

    return "".join(result)


def wrap_with_lstlisting(paragraph):
    return "\\begin{Verbatim}[tabsize=4]\n" + \
        wrap_string(paragraph, width=80, new_line_indent=True) + "\n\\end{Verbatim}"


def remove_figure_envs_from_latex(latex_content):
    # remove any figure environments from the given latex content
    latex_content = regex.sub(r'\\begin\{figure\}.*?\\end\{figure\}', '', latex_content, flags=regex.DOTALL)

    # find sentences that contain references to figures and remove them completely
    sentences = regex.findall(r'[^\.]*?\\ref\{fig:.*?\}[^\.]*?\.', latex_content)
    for sentence in sentences:
        latex_content = latex_content.replace(sentence, '')

    return latex_content


def clean_latex(latex_content):
    preamble = latex_content[:latex_content.find(r'\begin{document}')]
    appendices = latex_content[latex_content.find(r'\appendix'):]
    latex_content = latex_content[latex_content.find(r'\begin{document}'):latex_content.find(r'\appendix')]
    latex_content = remove_figure_envs_from_latex(latex_content)
    latex_content = preamble + replace_special_chars(latex_content) + appendices
    return latex_content


def evaluate_latex_num_command(latex_str):
    """
    Evaluates all expressions of the form \num{...} in the given latex string and replaces them with the result.
    """
    pattern = r'\\num{(.+?)}'
    matches = re.findall(pattern, latex_str)
    for match in matches:
        try:
            result = round(eval(match), 10)
            latex_str = latex_str.replace(f'\\num{{{match}}}', str(result))
        except (SyntaxError, NameError):
            pass
    return latex_str


def check_usage_of_unwanted_commands(latex_content: str, unwanted_commands: List[str] = None):
    unwanted_commands = unwanted_commands if unwanted_commands is not None else [r'\cite', r'\verb']
    unwanted_commands_used = [c for c in unwanted_commands if c in latex_content]
    if unwanted_commands_used:
        raise UnwantedCommandsUsedInLatex(unwanted_commands_used)


def check_non_latex_citations(latex_content: str):
    non_latex_citations = get_non_latex_citations(latex_content)
    if non_latex_citations:
        raise NonLatexCitations(non_latex_citations)


def check_latex_compilation(latex_content: str, file_stem: str = 'test', output_directory: Optional[str] = None,
                            tolerance_for_too_wide_in_pts: Optional[float] = None):
    with open(os.path.join(THIS_FOLDER, 'compilation_template.tex'), 'r') as f:
        latex_document = f.read().replace('@@@content@@@', latex_content)
    save_latex_and_compile_to_pdf(latex_document, file_stem, output_directory,
                                  tolerance_for_too_wide_in_pts=tolerance_for_too_wide_in_pts)


def save_latex_and_compile_to_pdf(latex_content: str, file_stem: str, output_directory: Optional[str] = None,
                                  references: Set[Citation] = None,
                                  tolerance_for_too_wide_in_pts: Optional[float] = None):
    latex_content = evaluate_latex_num_command(latex_content)
    references = references or set()
    should_compile_with_bib = len(references) > 0
    latex_file_name = file_stem + '.tex'
    pdflatex_params = ['pdflatex', '--shell-escape', '-interaction', 'nonstopmode', latex_file_name]
    with run_in_temp_directory():

        # Create the bib file:
        if should_compile_with_bib:
            references_bibtex = [reference.bibtex for reference in references]
            with open(BIB_FILENAME, 'w') as f:
                f.write('\n\n'.join(references_bibtex))

        with open(latex_file_name, 'w') as f:
            f.write(latex_content)
        try:
            pdflatex_output = subprocess.run(pdflatex_params,
                                             check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            raise LatexCompilationError(latex_content=latex_content, pdflatex_output=e.stdout.decode('utf-8'))

        output = pdflatex_output.stdout.decode('utf-8')
        if r'Overfull \hbox' in output:
            overflow_in_pt = float(re.search(r'Overfull \\hbox \((.*?)pt too wide\)', output).group(1))
            print('Overflow in pt: ', overflow_in_pt)
            if tolerance_for_too_wide_in_pts is not None and overflow_in_pt > tolerance_for_too_wide_in_pts:
                move_latex_and_pdf_to_output_directory(file_stem, output_directory, latex_file_name)
                raise TooWideTableOrText(latex_content=latex_content,
                                         pdflatex_output=pdflatex_output.stdout.decode('utf-8'))

        if should_compile_with_bib:
            try:
                subprocess.run(['bibtex', file_stem], check=True)
                subprocess.run(pdflatex_params, check=True)
                subprocess.run(pdflatex_params, check=True)
            except subprocess.CalledProcessError:
                move_latex_and_pdf_to_output_directory(file_stem, output_directory, latex_file_name)
                raise
        move_latex_and_pdf_to_output_directory(file_stem, output_directory, latex_file_name)


def move_latex_and_pdf_to_output_directory(file_stem: str, output_directory: str = None, latex_file_name: str = None):
    # Move the pdf and the latex and the citation file to the original directory:

    def move_if_exists(file_name):
        if os.path.exists(file_name):
            shutil.move(file_name, output_directory)

    if output_directory is not None:
        move_if_exists(file_stem + '.pdf')
        move_if_exists(latex_file_name)
        move_if_exists('citations.bib')
