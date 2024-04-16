import logging
import os
import re
import subprocess
import sys
from contextlib import contextmanager

from plasTeX.TeX import TeX
from plasTeX.Renderers.HTML5 import HTML5

from data_to_paper.utils.file_utils import run_in_temp_directory


def convert_latex_to_html(latex: str) -> str:
    """
    Convert LaTeX text to HTML using Pandoc through pypandoc.

    Parameters:
    - latex_text (str): A string containing LaTeX code.

    Returns:
    - str: The converted HTML text.
    """
    # check if pandoc is installed
    try:
        subprocess.run(['pandoc', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except FileNotFoundError:
        raise FileNotFoundError("Pandoc is not installed. Please install Pandoc to use this feature.")

    is_title = re.search(r'\\title{(.+?)}', latex)

    # Get the html template:
    if is_title:
        template_name = 'html_template_for_title_latex.html'
    else:
        template_name = 'html_template_for_titleless_latex.html'
    dir_path = os.path.dirname(os.path.realpath(__file__))
    template_path = os.path.join(dir_path, template_name)

    tex_file = 'temp.tex'
    # command = ['pandoc', '-s', tex_file, '-o', html_file]
    command = [
        'pandoc', '-s', tex_file,
        '--template', template_path]
    if not is_title:
        command += [
        '--metadata', 'title=Titleless LaTeX Document']
    command += [
        '-t', 'html']
    try:
        with run_in_temp_directory():
            with open(tex_file, 'w') as f:
                f.write(latex)
            return subprocess.check_output(command, universal_newlines=True)
    except subprocess.CalledProcessError as e:
        # Return html saying there was an error:
        return f'<html><body><h1>Error converting LaTeX to HTML</h1><p>{e}</p></body></html>'
