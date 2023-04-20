import os

from _pytest.fixtures import fixture

from scientistgpt.latex import latex_to_pdf


@fixture()
def latex_content():
    return r'''
\documentclass{article}
\begin{document}
Hello World!
\end{document}
'''


def test_latex_to_pdf(tmpdir, latex_content):
    pdf_file_path = tmpdir.join('test.pdf').strpath
    latex_to_pdf(latex_content, pdf_file_path)

    assert os.path.exists(pdf_file_path)
