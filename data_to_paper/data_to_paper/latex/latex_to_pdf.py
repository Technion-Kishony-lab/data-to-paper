import os
import shutil
import subprocess
import regex

from typing import Set, Optional, List

from data_to_paper.servers.crossref import CrossrefCitation
from data_to_paper.utils.file_utils import run_in_temp_directory

from .exceptions import LatexCompilationError, UnwantedCommandsUsedInLatex, TooWideTableOrText

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


def process_non_math_part(text):
    # Process non-math part and replace special characters if not already escaped
    processed_part = ""
    for i in range(len(text)):
        char = text[i]
        if char in CHARS and (i == 0 or text[i - 1] != '\\'):
            processed_part += CHARS[char]
        else:
            processed_part += char
    return processed_part


def replace_special_chars(text):
    result = []
    last_end = 0

    for match in regex.finditer(MATH_PATTERN, text, flags=regex.VERBOSE):
        non_math_part = text[last_end:match.start()]

        processed_part = process_non_math_part(non_math_part)
        result.append(processed_part)

        possibly_math_part = match.group()
        # find `\caption{...} parts in possibly_math_part and apply escaping on what's inside the curly braces
        math_part = regex.sub(r'\\caption\{.*?\}',
                              lambda m: m.group().replace(m.group(0)[9:-1], process_non_math_part(m.group(0)[9:-1])),
                              possibly_math_part)
        result.append(math_part)

        last_end = match.end()

    # Process the remaining non-math part after the last match
    non_math_part = text[last_end:]
    processed_part = process_non_math_part(non_math_part)
    result.append(processed_part)

    return "".join(result)


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
    latex_content = latex_content[latex_content.find(r'\begin{document}'):]
    latex_content = remove_figure_envs_from_latex(latex_content)
    latex_content = preamble + replace_special_chars(latex_content)
    return latex_content


def check_usage_of_unwanted_commands(latex_content: str, unwanted_commands: List[str] = None):
    unwanted_commands = unwanted_commands if unwanted_commands is not None else [r'\cite', r'\verb']
    unwanted_commands_used = [c for c in unwanted_commands if c in latex_content]
    if unwanted_commands_used:
        raise UnwantedCommandsUsedInLatex(unwanted_commands_used)


def check_latex_compilation(latex_content: str, file_stem: str = 'test', output_directory: Optional[str] = None):
    with open(os.path.join(THIS_FOLDER, 'compilation_template.tex'), 'r') as f:
        latex_document = f.read().replace('@@@content@@@', latex_content)
    save_latex_and_compile_to_pdf(latex_document, file_stem, output_directory, compile_check=True)


def save_latex_and_compile_to_pdf(latex_content: str, file_stem: str, output_directory: Optional[str] = None,
                                  references: Set[CrossrefCitation] = None, compile_check: bool = False):
    references = references or set()
    should_compile_with_bib = len(references) > 0
    latex_file_name = file_stem + '.tex'
    with run_in_temp_directory():

        # Create the bib file:
        if should_compile_with_bib:
            references_bibtex = [reference.bibtex for reference in references]
            with open(BIB_FILENAME, 'w') as f:
                f.write('\n\n'.join(references_bibtex))

        with open(latex_file_name, 'w') as f:
            f.write(latex_content)
        try:
            pdflatex_output = subprocess.run(['pdflatex', '-interaction', 'nonstopmode', latex_file_name],
                                             check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,)
        except subprocess.CalledProcessError as e:
            raise LatexCompilationError(latex_content=latex_content, pdflatex_output=e.stdout.decode('utf-8'))

        if r'Overfull \hbox' in pdflatex_output.stdout.decode('utf-8') and compile_check:
            raise TooWideTableOrText(latex_content=latex_content,
                                     pdflatex_output=pdflatex_output.stdout.decode('utf-8'))

        if should_compile_with_bib:
            subprocess.run(['bibtex', file_stem], check=True)
            subprocess.run(['pdflatex', '-interaction', 'nonstopmode', latex_file_name], check=True)
            subprocess.run(['pdflatex', '-interaction', 'nonstopmode', latex_file_name], check=True)

        # Move the pdf and the latex and the citation file to the original directory:
        if output_directory is not None:
            shutil.move(file_stem + '.pdf', output_directory)
            shutil.move(latex_file_name, output_directory)
            if should_compile_with_bib:
                shutil.move('citations.bib', output_directory)
