import os
import subprocess


def compile_latex_file_to_pdf(latex_file_path: str, should_compile_with_bib: bool = False):
    latex_file_path = os.path.abspath(latex_file_path)
    latex_file_name = os.path.basename(latex_file_path)
    os.chdir(os.path.dirname(latex_file_path))
    subprocess.run(['pdflatex', latex_file_name], check=True)
    if should_compile_with_bib:
        subprocess.run(['bibtex', latex_file_name.replace('.tex', '')], check=True)
        subprocess.run(['pdflatex', latex_file_name], check=True)
        subprocess.run(['pdflatex', latex_file_name], check=True)

    # pdflatex creates some additional files we don't need:
    for ext in ['.aux', '.log', '.out', '.bbl', '.blg']:
        if os.path.exists(latex_file_path.replace('.tex', ext)):
            os.remove(latex_file_path.replace('.tex', ext))


def save_latex_and_compile_to_pdf(latex_content: str, file_path: str, should_compile_with_bib: bool = False,
                                  should_compile_to_pdf: bool = True):
    with open(file_path + '.tex', 'w') as f:
        f.write(latex_content)
    if should_compile_to_pdf:
        compile_latex_file_to_pdf(file_path + '.tex', should_compile_with_bib)
