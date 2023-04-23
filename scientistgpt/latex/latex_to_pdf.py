import os
from typing import Optional


def compile_latex_file_to_pdf(latex_file_path: str, bib_file_name: Optional[str] = None):
    latex_file_path = os.path.abspath(latex_file_path)
    os.system(f'pdflatex -output-directory {os.path.dirname(latex_file_path)} {latex_file_path}')

    if bib_file_name is not None:
        os.system(f'bibtex {bib_file_name}')
        # We need to run pdflatex twice to get the references right:
        os.system(f'pdflatex -output-directory {os.path.dirname(latex_file_path)} {latex_file_path}')
        os.system(f'pdflatex -output-directory {os.path.dirname(latex_file_path)} {latex_file_path}')

    # pdflatex creates some additional files we don't need:
    for ext in ['.aux', '.log', '.out']:
        if os.path.exists(latex_file_path.replace('.tex', ext)):
            os.remove(latex_file_path.replace('.tex', ext))


def save_latex_and_compile_to_pdf(latex_content: str, file_path: str, bib_file_name: Optional[str] = None,
                                  should_compile_to_pdf: bool = True):
    with open(file_path + '.tex', 'w') as f:
        f.write(latex_content)
    if should_compile_to_pdf:
        compile_latex_file_to_pdf(file_path + '.tex', bib_file_name)
