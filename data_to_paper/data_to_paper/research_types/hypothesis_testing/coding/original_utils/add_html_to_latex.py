from typing import Optional

HTML_COMMENT_HEADER = "% HTML representation of the table:\n% \n% "


def convert_to_latex_comment(text: str) -> str:
    """
    Convert a string to a comment in latex.
    """
    return text.replace('\n', '\n% ')


def add_html_to_latex(latex: str, html: str) -> str:
    """
    Add an html as a comment to a latex code.
    """
    latex += '\n'
    latex += HTML_COMMENT_HEADER
    latex += convert_to_latex_comment(html)
    return latex


def get_html_from_latex(latex: str) -> Optional[str]:
    """
    Extract the html table from the comment of a latex table.
    """
    if HTML_COMMENT_HEADER not in latex:
        return None
    html = latex.split(HTML_COMMENT_HEADER)[1]
    # remove the leading comment character
    html = html.replace('\n% ', '\n')
    return html


def get_latex_without_html_comment(latex: str) -> str:
    """
    Remove the html comment from a latex table.
    """
    return latex.split(HTML_COMMENT_HEADER)[0]
