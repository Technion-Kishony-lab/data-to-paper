import os
import re
import subprocess

from data_to_paper.utils.subprocess_call import get_subprocess_kwargs
from data_to_paper.terminate.exceptions import MissingInstallationError
from data_to_paper.terminate.resource_checking import resource_checking
from data_to_paper.latex.clean_latex import process_latex_text_and_math
from data_to_paper.utils.file_utils import run_in_temp_directory
from data_to_paper.text.text_formatting import escape_html


@resource_checking("Checking Pandoc installation")
def check_pandoc_is_installed():
    # This will raise MissingInstallationError:
    raise_if_pandoc_is_not_installed()


def raise_if_pandoc_is_not_installed():
    try:
        subprocess.run(['pandoc', '--version'], **get_subprocess_kwargs(capture=False))
    except FileNotFoundError:
        raise MissingInstallationError(package_name="Pandoc", instructions="See: https://pandoc.org/installing.html")


def convert_latex_to_html(latex: str) -> str:
    """
    Convert LaTeX text to HTML using Pandoc through pypandoc.

    Parameters:
    - latex (str): A string containing LaTeX code.

    Returns:
    - str: The converted HTML text.
    """
    raise_if_pandoc_is_not_installed()

    is_title = re.search(pattern=r'\\title{(.+?)}', string=latex)
    dir_path = os.path.dirname(os.path.realpath(__file__))
    tex_file = 'temp.tex'
    command = [
        'pandoc', '-s', tex_file,
        '--lua-filter', os.path.join(dir_path, 'adjust_section.lua'),
        '-t', 'html'
    ]

    # Get the html template:
    if is_title:
        template_name = 'html_template_for_title_latex.html'
    else:
        template_name = 'html_template_for_titleless_latex.html'
    template_path = os.path.join(dir_path, template_name)
    command += ['--template', template_path]

    if not is_title:
        command += ['--metadata', 'title=Titleless LaTeX Document']

    # To show citation commands (like '\\cite{ref1}'):
    command += ['--citeproc']

    try:
        with run_in_temp_directory():
            # process latex and escape special characters
            latex = process_latex_text_and_math(latex)
            # Write the LaTeX into a temporary file
            with open(tex_file, 'w', encoding='utf-8') as f:
                f.write(latex)
            # Convert using Pandoc
            output = subprocess.run(command, universal_newlines=True, **get_subprocess_kwargs())
            return output.stdout
    except subprocess.CalledProcessError:
        # In case of an error, return the raw latex with proper escaping for HTML
        return escape_html(latex)
