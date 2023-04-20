import os


def compile_latex_file_to_pdf(latex_file_path: str):
    latex_file_path = os.path.abspath(latex_file_path)
    os.system(f'pdflatex -output-directory {os.path.dirname(latex_file_path)} {latex_file_path}')
    # pdflatex creates some additional files we don't need:
    for ext in ['.aux', '.log', '.out']:
        if os.path.exists(latex_file_path.replace('.tex', ext)):
            os.remove(latex_file_path.replace('.tex', ext))


def save_latex_and_compile_to_pdf(latex_content: str, file_path: str, should_compile_to_pdf: bool = True):
    with open(file_path + '.tex', 'w') as f:
        f.write(latex_content)
    if should_compile_to_pdf:
        compile_latex_file_to_pdf(file_path + '.tex')
