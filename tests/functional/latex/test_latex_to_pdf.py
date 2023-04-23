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


def create_citations_file(tmpdir):
    citations_file = tmpdir.join('citations.bib').strpath
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
    file_path = tmpdir.join('test').strpath
    save_latex_and_compile_to_pdf(latex_content, file_path)

    assert os.path.exists(file_path + '.tex')
    assert os.path.exists(file_path + '.pdf')
    assert not os.path.exists(file_path + '.aux')
    assert not os.path.exists(file_path + '.log')


def test_latex_to_pdf_with_bibtex(tmpdir, latex_content_with_citations):
    file_path = tmpdir.join('test').strpath
    create_citations_file(tmpdir)
    save_latex_and_compile_to_pdf(latex_content_with_citations, file_path, should_compile_with_bib=True)

    assert os.path.exists(file_path + '.tex')
    assert os.path.exists(file_path + '.pdf')
    assert not os.path.exists(file_path + '.blg')
    assert not os.path.exists(file_path + '.bbl')
    assert not os.path.exists(file_path + '.aux')
    assert not os.path.exists(file_path + '.log')
