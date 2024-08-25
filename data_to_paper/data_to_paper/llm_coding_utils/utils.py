from pathlib import Path


def convert_to_latex_comment(text: str) -> str:
    """
    Convert a string to a comment in latex.
    """
    lines = text.split('\n')
    return '% ' + '\n% '.join(lines)
