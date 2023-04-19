import os
from typing import Dict


def load_paper_template(template_filename: str):
    """
    Load the specified template file.
    """
    template_path = os.path.join(os.path.dirname(__file__), f'templates/{template_filename}')
    with open(template_path, 'r') as f:
        paper_template = f.read()
    return paper_template


def assemble_latex_paper_from_sections(template_name: str, section_names_to_content: Dict[str, str]) -> str
    """
    Assemble a paper from the different sections.
    """

    paper_template = load_paper_template(template_name)
    # replace each section with the corresponding section.
    # In the paper template the sections are marked with @@@section_name@@@

    for section_name, section_content in section_names_to_content.items():
        paper_template = paper_template.replace(f'@@@{section_name}@@@', section_content)
    return paper_template


def save_latex_and_compile_to_pdf(latex_text: str, filename: str):
    """
    Compile latex to a pdf file.
    """
    with open(filename, 'w') as f:
        f.write(latex_text)
    os.system(f'pdflatex {filename}')
