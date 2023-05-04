import pytest

from g3pt.latex import extract_latex_section_from_response, FailedToExtractLatexContent

response_with_latex_title = r"""
here is the title
\title{The most amazing title ever}
I think this title fits the paper perfectly.
"""

response_with_wrong_latex_title = r"""
here is the title
\title{The most amazing title ever
I think this title fits the paper perfectly.
"""

response_with_latex_abstract = r"""
here is the abstract
\begin{abstract}The most amazing abstract ever\end{abstract}
I think this abstract fits the paper perfectly.
"""


response_with_latex_section = r"""
here is the section
\section{Introduction}This is the introduction
"""


response_with_starred_latex_section = r"""
here is the section
\section*{Introduction}This is the introduction
"""


def test_extract_latex_title_from_response():
    assert extract_latex_section_from_response(response_with_latex_title, 'title') == \
           r'\title{The most amazing title ever}'


def test_extract_latex_abstract_from_response_as_plan_text():
    assert extract_latex_section_from_response(response_with_latex_abstract, 'abstract', as_latex=False) == \
           'The most amazing abstract ever'


def test_extract_latex_fail_to_extract_title_from_response():
    with pytest.raises(FailedToExtractLatexContent):
        extract_latex_section_from_response(response_with_wrong_latex_title, 'title')


def test_extract_latex_section_from_response_as_plan_text():
    assert extract_latex_section_from_response(response_with_latex_section, 'introduction', as_latex=False) == \
           'This is the introduction\n'


def test_extract_latex_starred_section_from_response_as_plan_text():
    assert extract_latex_section_from_response(response_with_starred_latex_section, 'introduction', as_latex=False) == \
           'This is the introduction\n'
