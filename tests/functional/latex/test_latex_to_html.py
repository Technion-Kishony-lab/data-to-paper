from data_to_paper.latex.latex_to_html import convert_latex_to_html


def test_convert_latex_to_html():
    latex = r"""
\section{Hello}
Hello, world!
"""
    html = convert_latex_to_html(latex)
    assert '>Hello</h2>' in html
    assert '>Hello, world!</p>' in html
