import os


def get_paper_template_path(template_file: str) -> str:
    """
    Get the path to the template file.
    """
    return os.path.join(os.path.dirname(__file__), 'templates', template_file)
