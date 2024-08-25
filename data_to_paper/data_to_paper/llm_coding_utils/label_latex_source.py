from typing import Optional

DISPLAYITEM_COMMENT_HEADER = '% This latex displayitem was generated from: '


def extract_source_filename_from_latex_displayitem(latex: str) -> Optional[str]:
    """
    Extract the source filename from a latex table/figure.
    """
    first_line = latex.split('\n')[0]
    if not first_line.startswith(DISPLAYITEM_COMMENT_HEADER):
        return None
    filename = first_line.split('`')[1]
    return filename


def embed_source_filename_as_comment_in_latex_displayitem(filename: str) -> str:
    """
    Add the source filename to a latex table/figure.
    """
    return DISPLAYITEM_COMMENT_HEADER + f'`{filename}`\n'
