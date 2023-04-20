import os

from _pytest.fixtures import fixture

from scientistgpt.latex import save_latex_and_compile_to_pdf


@fixture()
def latex_content():
    return r'''
\documentclass{article}
\begin{document}
Hello World!
\end{document}
'''


def test_latex_to_pdf(tmpdir, latex_content):
    file_path = tmpdir.join('test').strpath
    save_latex_and_compile_to_pdf(latex_content, file_path)

    assert os.path.exists(file_path + '.tex')
    assert os.path.exists(file_path + '.pdf')
    assert not os.path.exists(file_path + '.aux')
    assert not os.path.exists(file_path + '.log')
