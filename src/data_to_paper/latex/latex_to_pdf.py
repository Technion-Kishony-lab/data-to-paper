import os
import re
import shutil
import subprocess
import fitz  # PyMuPDF
import numpy as np

from typing import Optional, Collection, Tuple, Dict

from pathlib import Path

from data_to_paper.utils.subprocess_call import get_subprocess_kwargs
from data_to_paper.terminate.exceptions import MissingInstallationError
from data_to_paper.servers.custom_types import Citation
from data_to_paper.utils.file_utils import run_in_temp_directory
from data_to_paper.code_and_output_files.ref_numeric_values import replace_hyperlinks_with_values
from data_to_paper.text.text_extractors import extract_all_external_brackets

from .exceptions import LatexCompilationError, LatexNumCommandFormulaEvalError, \
    LatexNestedNumCommandError, LatexNumCommandNoExplanation, PlainNumberLatexNumCommandError

BIB_FILENAME: str = 'citations.bib'
WATERMARK_PATH: str = os.path.join(os.path.dirname(__file__), 'watermark.pdf')

PDFLATEX_INSTALLATION_INSTRUCTIONS = r"""
Installations instructions for pdflatex:

* **On Ubuntu**:
```
sudo apt-get update && \
sudo apt-get install -y --no-install-recommends \
texlive-latex-base \
texlive-latex-extra \
texlive-fonts-recommended
```

* **On MacOS**:
- Ensure you have Homebrew installed (see https://brew.sh).
- Install MacTeX with the following command:
```
brew install --cask mactex-no-gui
```
- After installation, you may need to add the TeX binaries to your PATH!

* **On Windows**:
- Download and install MiKTeX from https://miktex.org/download.
- During installation, select 'Yes' when asked to install missing packages on-the-fly.
- After installation, you may need to add the TeX binaries to your PATH!
 """


def is_pdflatex_installed() -> Optional[bool]:
    """
    Check that pdflatex is installed.
    True if installed, False if not.
    None if check failed.
    """
    try:
        subprocess.run(['pdflatex', '--version'], **get_subprocess_kwargs(capture=False))
    except FileNotFoundError:
        return False
    except subprocess.CalledProcessError:
        return None
    return True


def is_pdflatex_package_installed(package: str) -> Optional[bool]:
    """
    Check that the packages used in the latex document are installed.
    True if installed, False if not.
    None if check failed.
    """
    try:
        subprocess.run(['kpsewhich', package + '.sty'], **get_subprocess_kwargs(capture=False))
    except FileNotFoundError:
        return None
    except subprocess.CalledProcessError:
        return False
    return True


def is_string_plain_number(string: str) -> bool:
    try:
        float(string)
    except ValueError:
        return False
    return True


def evaluate_latex_num_command(latex_str, ref_prefix='', enforce_explanation: bool = True,
                               just_strip_explanation: bool = False,
                               ) -> Tuple[str, Dict[str, str]]:
    r"""
    Evaluates all expressions of the form \num{formula} or \num{formula, "explanation"} in the given latex string
    and replaces them with the result of the formula.
    if ref_prefix, then add \hyperlink{ref_prefix?}{result}, where ? is the index of the expression.
    Return the new latex string and a mapping from the index to "expression = result".
    """
    command = r'\num{'
    matches = extract_all_external_brackets(latex_str, '{', '}', open_phrase=command)
    labels_to_notes = {}
    for index, full_match in enumerate(matches):
        match = full_match[len(command):-1]  # remove the command and the closing bracket
        match = match.strip()
        if command in match:
            raise LatexNestedNumCommandError(expression=full_match)
        # separate <formula>, "explanation" into formula and explanation:
        if match.endswith('"'):
            open_quote_index = match[:-1].rfind('"')
            comma_index = match[:open_quote_index].rfind(',')
            explanation = match[open_quote_index + 1:-1]
            formula = match[:comma_index]
        else:
            explanation = None
            formula = match

        formula_without_hyperlinks = replace_hyperlinks_with_values(formula)
        if is_string_plain_number(formula_without_hyperlinks):
            raise PlainNumberLatexNumCommandError(expression=full_match)
        if enforce_explanation and explanation is None:
            raise LatexNumCommandNoExplanation(expression=full_match)
        if just_strip_explanation:
            replace_with = command + formula_without_hyperlinks + '}'
            latex_str = latex_str.replace(command + match + '}', replace_with)
            continue
        try:
            result = eval(formula_without_hyperlinks,
                          {'exp': np.exp, 'log': np.log, 'sin': np.sin, 'cos': np.cos, 'tan': np.tan, 'pi': np.pi,
                           'e': np.e, 'sqrt': np.sqrt, 'log2': np.log2, 'log10': np.log10})
        except Exception as e:
            raise LatexNumCommandFormulaEvalError(expression=match, exception=e)
        if isinstance(result, float):
            result = '{:.4g}'.format(result)
        else:
            result = str(result)
        label = f'{ref_prefix}{index}'
        if ref_prefix:
            replace_with = f'\\hyperlink{{{label}}}{{{result}}}'
        else:
            replace_with = result
        latex_str = latex_str.replace(command + match + '}', replace_with)
        note = f'{formula} = {result}'
        if explanation:
            note += f'\n\n{explanation}'
            # note += f'     {explanation}'
        labels_to_notes[label] = note
    return latex_str, labels_to_notes


def add_watermark_to_pdf(pdf_path: str, watermark_path: str, output_path: str = None):
    """
    Add watermark to each page of a PDF while preserving hyperlinks using PyMuPDF (fitz).
    :param pdf_path: Path to the PDF file to be watermarked.
    :param watermark_path: Path to the watermark PDF file. The first page of this file will be used as the watermark.
    :param output_path: Path for the output watermarked PDF file. If None, the original PDF will be overwritten.
    """
    if output_path is None:
        output_path = pdf_path

    with fitz.open(pdf_path) as pdf_doc, fitz.open(watermark_path) as watermark_doc:
        for page in pdf_doc:
            # Overlay the watermark onto the page by adding the XObject
            page.show_pdf_page(page.rect, watermark_doc, 0)

        # Save the watermarked PDF
        pdf_doc.save(output_path, incremental=True, encryption=0)


def _get_over_width_pts(pdflatex_output: str) -> Optional[float]:
    match = re.search(pattern=r'Overfull \\hbox \((.*?)pt too wide\)', string=pdflatex_output)
    if match:
        return float(match.group(1))
    return None


def save_latex_and_compile_to_pdf(latex_content: str, file_stem: str, output_directory: Optional[str] = None,
                                  references: Collection[Citation] = None, format_cite: bool = True,
                                  figures_folder: Optional[Path] = None,
                                  ) -> Tuple[str, Optional[float]]:
    references = references or set()
    should_compile_with_bib = len(references) > 0
    latex_file_name = file_stem + '.tex'
    pdflatex_params = ['pdflatex', '--shell-escape', '-interaction=nonstopmode', latex_file_name]
    with run_in_temp_directory():
        # Copy the figures from the output directory to the temp directory:
        if figures_folder is not None:
            png_files_in_running_directory = [f for f in figures_folder.glob('*.png') if f.is_file()]
            for png_file in png_files_in_running_directory:
                shutil.copy(png_file, '.')

        # Create the bib file:
        if should_compile_with_bib:
            references_bibtex = [reference.bibtex for reference in references]
            with open(BIB_FILENAME, 'w', encoding='utf-8') as f:
                f.write('\n\n'.join(references_bibtex))

        with open(latex_file_name, 'w', encoding='utf-8') as f:
            f.write(latex_content)
        try:
            pdflatex_output = subprocess.run(pdflatex_params, **get_subprocess_kwargs())
        except FileNotFoundError:
            raise MissingInstallationError(package_name="pdflatex", instructions=PDFLATEX_INSTALLATION_INSTRUCTIONS)
        except subprocess.CalledProcessError as e:
            _move_latex_and_pdf_to_output_directory(file_stem, output_directory, latex_file_name)
            raise LatexCompilationError(latex_content=latex_content,
                                        pdflatex_output=e.stdout.decode('utf-8', errors='replace'))

        pdflatex_output = pdflatex_output.stdout.decode('utf-8', errors='replace')

        if format_cite:
            try:
                if should_compile_with_bib:
                    try:
                        subprocess.run(['bibtex', file_stem], **get_subprocess_kwargs(capture=False))
                    except FileNotFoundError:
                        raise MissingInstallationError(package_name="bibtex",
                                                       instructions=PDFLATEX_INSTALLATION_INSTRUCTIONS)
                subprocess.run(pdflatex_params, **get_subprocess_kwargs(capture=False))
                subprocess.run(pdflatex_params, **get_subprocess_kwargs(capture=False))
            except subprocess.CalledProcessError:
                _move_latex_and_pdf_to_output_directory(file_stem, output_directory, latex_file_name)
                raise

        add_watermark_to_pdf(file_stem + '.pdf', WATERMARK_PATH)

        _move_latex_and_pdf_to_output_directory(file_stem, output_directory, latex_file_name)
        over_width_pts = _get_over_width_pts(pdflatex_output)
        return pdflatex_output, over_width_pts


def _move_latex_and_pdf_to_output_directory(file_stem: str, output_directory: str = None, latex_file_name: str = None):
    # Move the pdf and the latex and the citation file to the original directory:

    def move_if_exists(file_name):
        if os.path.exists(file_name):
            # delete older file if exists (this happen when we reset from the compilation step to earlier step)
            file_path = os.path.join(output_directory, file_name)
            if os.path.exists(file_path):
                os.remove(file_path)
            shutil.move(file_name, output_directory)

    if output_directory is not None:
        move_if_exists(file_stem + '.pdf')
        move_if_exists(latex_file_name)
        move_if_exists('citations.bib')
