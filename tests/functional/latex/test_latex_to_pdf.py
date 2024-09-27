import os

import pytest
from pytest import fixture

from data_to_paper.latex.clean_latex import process_latex_text_and_math
from data_to_paper.latex.exceptions import LatexCompilationError
from data_to_paper.latex.latex_doc import LatexDocument
from data_to_paper.latex.latex_to_pdf import evaluate_latex_num_command, save_latex_and_compile_to_pdf
from data_to_paper.servers.crossref import CrossrefCitation


@fixture()
def latex_content():
    return r'''
\documentclass{article}
\begin{document}
Hello World!
\end{document}
'''


@fixture()
def wrong_latex_content():
    return r'''
\documentclass{article}
\begin{document}
Hello & World!
\end{document}
'''


@fixture()
def latex_content_with_citations():
    return r'''
\documentclass{article}
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


@fixture()
def latex_content_with_hyperlinks():
    return r'''
\documentclass{article}
\usepackage[colorlinks]{hyperref}
\begin{document}
\section{A section}
Content with a hyperlink to some later \hyperlink{linkB}{\hypertarget{linkA}{content}}.

\clearpage
\section{Another section}
Content with a hyperlink to some earlier \hypertarget{linkB}{\hyperlink{linkA}{content}}.  
\end{document}
'''


@fixture()
def citations():
    return {
        CrossrefCitation(
            type='article',
            title='Citation 1',
            author='Author 1',
            first_author_family='AuthorFamily1',
            journal='Journal 1',
            year='2020',
            volume='1',
            number='1',
            pages='1-1',
            doi='10.1111/1111',
            url='https://www.example.com/1'
        ),
        CrossrefCitation(
            type='article',
            title='Citation 2',
            author='Author 2',
            first_author_family='AuthorFamily2',
            journal='Journal 2',
            year='2020',
            volume='2',
            number='2',
            pages='2-2',
            doi='10.1111/2222',
            url='https://www.example.com/2'
        )
    }


file_name = 'test'


def test_latex_document_is_hashable():
    assert hash(LatexDocument()) is not None


def test_latex_to_pdf(tmpdir, latex_content):
    save_latex_and_compile_to_pdf(latex_content, file_name, tmpdir.strpath)

    assert os.path.exists(os.path.join(tmpdir.strpath, file_name + '.tex'))
    assert os.path.exists(os.path.join(tmpdir.strpath, file_name + '.pdf'))
    assert not os.path.exists(os.path.join(tmpdir.strpath, file_name + '.aux'))
    assert not os.path.exists(os.path.join(tmpdir.strpath, file_name + '.log'))


def test_latex_to_pdf_with_bibtex(tmpdir, latex_content_with_citations, citations):
    save_latex_and_compile_to_pdf(latex_content_with_citations, file_name, tmpdir.strpath, citations)

    assert os.path.exists(os.path.join(tmpdir.strpath, file_name + '.tex'))
    assert os.path.exists(os.path.join(tmpdir.strpath, file_name + '.pdf'))
    assert os.path.exists(os.path.join(tmpdir.strpath, 'citations.bib'))
    assert not os.path.exists(os.path.join(tmpdir.strpath, file_name + '.aux'))
    assert not os.path.exists(os.path.join(tmpdir.strpath, file_name + '.log'))


def test_latex_to_pdf_error_handling(tmpdir, latex_content_with_unescaped_characters):
    save_latex_and_compile_to_pdf(
        process_latex_text_and_math(latex_content_with_unescaped_characters), file_name, tmpdir.strpath, )
    assert os.path.exists(os.path.join(tmpdir.strpath, file_name + '.tex'))
    assert os.path.exists(os.path.join(tmpdir.strpath, file_name + '.pdf'))
    assert not os.path.exists(os.path.join(tmpdir.strpath, file_name + '.aux'))
    assert not os.path.exists(os.path.join(tmpdir.strpath, file_name + '.log'))


def test_latex_to_pdf_with_hyperlinks(tmpdir, latex_content_with_hyperlinks):
    save_latex_and_compile_to_pdf(latex_content_with_hyperlinks, file_name, tmpdir.strpath)
    assert os.path.exists(os.path.join(tmpdir.strpath, file_name + '.tex'))
    assert os.path.exists(os.path.join(tmpdir.strpath, file_name + '.pdf'))


@pytest.mark.parametrize('latex, expected', [
    ('Hello & World!', r'Hello \& World!'),
    ('Hello % World!', r'Hello \% World!'),
    ('Hello # World!', r'Hello \# World!'),
    ('Hello _ World!', r'Hello \_ World!'),
])
def test_clean_latex(latex, expected):
    assert process_latex_text_and_math(latex) == expected


def test_latex_to_pdf_exception(tmpdir, wrong_latex_content):
    with pytest.raises(LatexCompilationError) as e:
        save_latex_and_compile_to_pdf(wrong_latex_content, file_name, tmpdir.strpath)
    e = e.value
    assert e.latex_content == wrong_latex_content
    assert e.get_latex_exception_line_number() == 3


@pytest.mark.parametrize('latex, expected', [
    (r'I have \num{1+2, "trivial"} apples.', ('I have 3 apples.', {'0': '1+2 = 3\n\ntrivial'})),
    (r'I have \num{1e3+2, "trivial"} apples.', ('I have 1002 apples.', {'0': '1e3+2 = 1002\n\ntrivial'})),
    (r'must be rounded \num{7.95 - 3.64, "diff"}.', ('must be rounded 4.31.', {'0': '7.95 - 3.64 = 4.31\n\ndiff'})),
])
def test_evaluate_latex_expression(latex, expected):
    latex, num_dict = evaluate_latex_num_command(latex)
    assert latex == expected[0]
    assert num_dict == expected[1]
    LatexDocument().compile_document(latex, file_stem='test')
