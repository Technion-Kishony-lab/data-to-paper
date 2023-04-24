import os
import shutil
from contextlib import contextmanager
from pathlib import Path
import subprocess


# Temp directory for latex complication:
module_dir = os.path.dirname(__file__)
TEMP_FOLDER_FOR_LATEX_COMPILE = (Path(module_dir) / 'temp_latex_compile').absolute()


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
                                  should_compile_with_bib: bool = False,
                                  should_compile_to_pdf: bool = True):
    latex_file_name = file_name + '.tex'
    with run_in_temp_directory():
        with open(latex_file_name, 'w') as f:
            f.write(latex_content)
        if should_compile_to_pdf:
            subprocess.run(['pdflatex', latex_file_name], check=True)
            if should_compile_with_bib:
                subprocess.run(['bibtex', file_name], check=True)
                subprocess.run(['pdflatex', latex_file_name], check=True)
                subprocess.run(['pdflatex', latex_file_name], check=True)

        # Move the pdf and the latex and the citation file to the original directory:
        shutil.move(file_name + '.pdf', output_directory)
        shutil.move(latex_file_name, output_directory)
        if should_compile_with_bib:
            shutil.move('citations.bib', output_directory)
