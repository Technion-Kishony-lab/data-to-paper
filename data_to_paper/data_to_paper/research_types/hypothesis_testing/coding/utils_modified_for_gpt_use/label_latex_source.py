from typing import Optional

TABLE_COMMENT_HEADER = '% This latex table was generated from: '


def extract_source_filename_from_latex(latex: str) -> Optional[str]:
    """
    Extract the source filename from a latex table.
    """
    first_line = latex.split('\n')[0]
    if not first_line.startswith(TABLE_COMMENT_HEADER):
        return None
    filename = first_line.split('`')[1]
    return filename


def wrap_source_filename_as_latex_comment(filename: str) -> str:
    """
    Add the source filename to a latex table.
    """
    return TABLE_COMMENT_HEADER + f'`{filename}`\n'
