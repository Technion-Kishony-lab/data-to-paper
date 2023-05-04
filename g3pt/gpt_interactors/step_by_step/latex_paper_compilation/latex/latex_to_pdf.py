import os
import shutil
from contextlib import contextmanager
from pathlib import Path
import subprocess
import regex

# Temp directory for latex complication:
module_dir = os.path.dirname(__file__)
TEMP_FOLDER_FOR_LATEX_COMPILE = (Path(module_dir) / 'temp_latex_compile').absolute()

CHARS = {
    '&': r'\&',
    '%': r'\%',
    '#': r'\#',
    '_': r'\_',
    '~': r'\textasciitilde',
    '^': r'\textasciicircum',
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
  (\\begin\{(?:figure|table)\})|
  # group 6, match non-typesetting commands
  (\\(?:ref|label)\{)
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
    (?(5)\\end\{(?:figure|table)\}|
    # else, match end of non-typesetting command
    \})
  )
)))))
"""


def replace_special_chars(text):
    result = []
    last_end = 0

    for match in regex.finditer(MATH_PATTERN, text, flags=regex.VERBOSE):
        non_math_part = text[last_end:match.start()]

        # Process non-math part and replace special characters if not already escaped
        processed_part = ""
        i = 0
        while i < len(non_math_part):
            char = non_math_part[i]
            if char in CHARS and (i == 0 or non_math_part[i - 1] != '\\'):
                processed_part += CHARS[char]
            else:
                processed_part += char
            i += 1

        result.append(processed_part)

        math_part = match.group()
        result.append(math_part)

        last_end = match.end()

    # Process the remaining non-math part after the last match
    non_math_part = text[last_end:]
    processed_part = ""
    i = 0
    while i < len(non_math_part):
        char = non_math_part[i]
        if char in CHARS and (i == 0 or non_math_part[i - 1] != '\\'):
            processed_part += CHARS[char]
        else:
            processed_part += char
        i += 1
    result.append(processed_part)

    return "".join(result)


@contextmanager
def run_in_temp_directory():
    cwd = os.getcwd()
    if not os.path.exists(TEMP_FOLDER_FOR_LATEX_COMPILE):
        os.mkdir(TEMP_FOLDER_FOR_LATEX_COMPILE)
    os.chdir(TEMP_FOLDER_FOR_LATEX_COMPILE)
    try:
        yield
    finally:
        os.chdir(cwd)
        shutil.rmtree(TEMP_FOLDER_FOR_LATEX_COMPILE)


def save_latex_and_compile_to_pdf(latex_content: str, file_name: str, output_directory: str,
                                  should_compile_with_bib: bool = False):
    latex_file_name = file_name + '.tex'
    latex_content = replace_special_chars(latex_content)
    with run_in_temp_directory():
        with open(latex_file_name, 'w') as f:
            f.write(latex_content)
        subprocess.run(['pdflatex', '-interaction', 'nonstopmode', latex_file_name], check=True)
        if should_compile_with_bib:
            # if citations file not in current directory copy it from output directory:
            if not os.path.exists('citations.bib'):
                shutil.copy(os.path.join(output_directory, 'citations.bib'), 'citations.bib')
            subprocess.run(['bibtex', file_name], check=True)
            subprocess.run(['pdflatex', '-interaction', 'nonstopmode', latex_file_name], check=True)
            subprocess.run(['pdflatex', '-interaction', 'nonstopmode', latex_file_name], check=True)

        # Move the pdf and the latex and the citation file to the original directory:
        shutil.move(file_name + '.pdf', output_directory)
        shutil.move(latex_file_name, output_directory)
        if should_compile_with_bib and not os.path.exists(os.path.join(output_directory, 'citations.bib')):
            shutil.move('citations.bib', output_directory)
