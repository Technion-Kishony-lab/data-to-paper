import os
import re
import subprocess

from data_to_paper.latex.clean_latex import process_latex_text_and_math
from data_to_paper.utils.file_utils import run_in_temp_directory
from data_to_paper.utils.text_formatting import escape_html


def convert_latex_to_html(latex: str) -> str:
    """
    Convert LaTeX text to HTML using Pandoc through pypandoc.

    Parameters:
    - latex (str): A string containing LaTeX code.

    Returns:
    - str: The converted HTML text.
    """

    from data_to_paper.research_types.hypothesis_testing.coding.original_utils.add_html_to_latex import \
        get_html_from_latex
    html = get_html_from_latex(latex)
    if html:
        return html

    # check if pandoc is installed
    try:
        subprocess.run(['pandoc', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except FileNotFoundError:
        raise FileNotFoundError("Pandoc is not installed. Please install Pandoc to use this feature.")

    is_title = re.search(r'\\title{(.+?)}', latex)
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
            with open(tex_file, 'w') as f:
                f.write(latex)
            # Convert using Pandoc
            html_output = subprocess.check_output(command, universal_newlines=True)
            return html_output
    except subprocess.CalledProcessError:
        # In case of an error, return the raw latex with proper escaping for HTML
        return escape_html(latex)
