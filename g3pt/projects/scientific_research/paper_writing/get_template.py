import os
from typing import List


def get_paper_template_path(template_file: str) -> str:
    """
    Get the path to the template file.
    """
    return os.path.join(os.path.dirname(__file__), 'templates', template_file)


def get_paper_template(template_file: str) -> str:
    """
    Load the specified template file.
    """
    with open(get_paper_template_path(template_file), 'r') as f:
        return f.read()


def get_paper_section_names(template_file: str) -> List[str]:
    """
    Get the sections of the paper from the template.
    Sections are flaked as: @@@section_name@@@
    """
    return get_paper_template(template_file).split('@@@')[1::2]
