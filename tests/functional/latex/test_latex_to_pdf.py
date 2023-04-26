import os
from pathlib import Path

from _pytest.fixtures import fixture

from scientistgpt.latex import save_latex_and_compile_to_pdf
from scientistgpt.latex.latex_to_pdf import TEMP_FOLDER_FOR_LATEX_COMPILE


@fixture()
def latex_content():
    return r'''
\documentclass{article}
\begin{document}
Hello World!
\end{document}
'''


@fixture()
def latex_content_with_citations():
    return r'''
\documentclass{article}
\usepackage{cite}
\usepackage{hyperref}
\begin{document}
Hello World! \cite{cite1} \cite{cite2}
\bibliographystyle{plain}
\bibliography{citations}
\end{document}
'''


@fixture()
def latex_content_with_unescaped_characters():
    return r'''
\documentclass{article}
\begin{document}
Hello World!
forgot to escape this underline: _
forgot to escape this hash: #
forgot to escape this percent: %
forgot to escape this ampersand: &
forgot to escape this tilde: ~
forgot to escape this caret: ^
already escaped this underscore: \_
also some math to test: $x^2$
math with two dollar signs: $$x^2$$
\end{document}
'''


def create_citations_file(path_to_citations_file):
    citations_file = Path(os.path.join(path_to_citations_file, 'citations.bib'))
    with open(citations_file, 'w') as f:
        f.write(r'''
@article{cite1,
    title={Citation 1},
    author={Author 1},
    journal={Journal 1},
    year={2020},
    volume={1},
    number={1},
    pages={1-1},
    doi={10.1111/1111},
    url={https://www.example.com/1}
}

@article{cite2,
    title={Citation 2},
    author={Author 2},
    journal={Journal 2},
    year={2020},
    volume={2},
    number={2},
    pages={2-2},
    doi={10.1111/2222},
    url={https://www.example.com/2}
}
''')


def test_latex_to_pdf(tmpdir, latex_content):
    output_directory = str(TEMP_FOLDER_FOR_LATEX_COMPILE)
    if not os.path.exists(output_directory):
        os.mkdir(output_directory)
    file_name = 'test'
    save_latex_and_compile_to_pdf(latex_content, file_name, tmpdir.strpath, should_compile_with_bib=False)

    assert os.path.exists(os.path.join(tmpdir.strpath, file_name + '.tex'))
    assert os.path.exists(os.path.join(tmpdir.strpath, file_name + '.pdf'))
    assert not os.path.exists(os.path.join(tmpdir.strpath, file_name + '.aux'))
    assert not os.path.exists(os.path.join(tmpdir.strpath, file_name + '.log'))


def test_latex_to_pdf_with_bibtex(tmpdir, latex_content_with_citations):
    output_directory = str(TEMP_FOLDER_FOR_LATEX_COMPILE)
    if not os.path.exists(output_directory):
        os.mkdir(output_directory)
    file_name = 'test'
    create_citations_file(output_directory)
    save_latex_and_compile_to_pdf(latex_content_with_citations, file_name, tmpdir.strpath,
                                  should_compile_with_bib=True)

    assert os.path.exists(os.path.join(tmpdir.strpath, file_name + '.tex'))
    assert os.path.exists(os.path.join(tmpdir.strpath, file_name + '.pdf'))
    assert os.path.exists(os.path.join(tmpdir.strpath, 'citations.bib'))
    assert not os.path.exists(os.path.join(tmpdir.strpath, file_name + '.aux'))
    assert not os.path.exists(os.path.join(tmpdir.strpath, file_name + '.log'))


def test_latex_to_pdf_error_handling(tmpdir, latex_content_with_unescaped_characters):
    output_directory = str(TEMP_FOLDER_FOR_LATEX_COMPILE)
    if not os.path.exists(output_directory):
        os.mkdir(output_directory)
    file_name = 'test'
    create_citations_file(output_directory)
    save_latex_and_compile_to_pdf(latex_content_with_unescaped_characters, file_name, tmpdir.strpath,
                                  should_compile_with_bib=False)

    assert os.path.exists(os.path.join(tmpdir.strpath, file_name + '.tex'))
    assert os.path.exists(os.path.join(tmpdir.strpath, file_name + '.pdf'))
    assert not os.path.exists(os.path.join(tmpdir.strpath, file_name + '.aux'))
    assert not os.path.exists(os.path.join(tmpdir.strpath, file_name + '.log'))
