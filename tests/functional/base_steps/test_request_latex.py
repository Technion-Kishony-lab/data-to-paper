from dataclasses import dataclass
from functools import partial
from typing import List

import pytest

from data_to_paper.base_steps import LatexReviewBackgroundProductsConverser
from data_to_paper.servers.llm_call import OPENAI_SERVER_CALLER
from data_to_paper.text import wrap_as_block

from .utils import TestProductsReviewGPT, check_wrong_and_right_responses


wrap_latex = partial(wrap_as_block, header='latex')


@dataclass
class TestLatexReviewBackgroundProductsConverser(TestProductsReviewGPT, LatexReviewBackgroundProductsConverser):
    max_reviewing_rounds: int = 0
    allowed_bibtex_citation_ids: list = None

    def _get_allowed_bibtex_citation_ids(self) -> List[str]:
        return self.allowed_bibtex_citation_ids or []


correct_table = r"""\begin{table}[h!]
\centering
 \begin{tabular}{||c c c c||}
 \hline
 Col1 & Col2 & Col2 & Col3 \\ [0.5ex] 
 \hline\hline
 1 & 6 & 87837 & 787 \\ 
 2 & 7 & 78 & 5415 \\
 3 & 545 & 778 & 7507 \\
 4 & 545 & 18744 & 7560 \\
 5 & 88 & 788 & 6344 \\ [1ex] 
 \hline
 \end{tabular}
 \caption{\label{demo-table}My title.}
\end{table}"""


correct_title = r'\title{The ultimate title}'

correct_abstract = r'\begin{abstract}The ultimate abstract\end{abstract}'


@pytest.mark.parametrize('correct_latex, section', [
    # (correct_table, 'table'),
    (correct_title, 'title'),
    (correct_abstract, 'abstract'),
])
def test_request_latex_with_correct_answer(correct_latex, section):
    check_wrong_and_right_responses(
        [f'Here is the correct latex:\n{correct_latex}\nShould be all good.'],
        requester=TestLatexReviewBackgroundProductsConverser(section_names=[section]),
        correct_value=[correct_latex])


@pytest.mark.parametrize('correct_latex, section, replaced_value, replace_with, corrected', [
    (correct_title, 'title', 'The ultimate', 'The & ultimate', r'The \& ultimate'),
])
def test_request_latex_autocorrect(correct_latex, section, replaced_value, replace_with, corrected):
    incorrect_latex = correct_latex.replace(replaced_value, replace_with)
    corrected_latex = incorrect_latex.replace(replace_with, corrected)
    check_wrong_and_right_responses(
        [f'Here is some wrong latex:\n{incorrect_latex}\nYou should correct it yourself.'],
        requester=TestLatexReviewBackgroundProductsConverser(section_names=[section]),
        correct_value=[corrected_latex])


@pytest.mark.parametrize('correct_latex, section, replaced_value, replace_with, error_includes', [
    # failed extractions:
    # (correct_table, 'table', r'\begin{table}', r'\begin', (r'Failed to extract table from response',)),
    (correct_title, 'title', '}', '', (r'Failed to extract title from response',)),

    # failed compilations:
    # (correct_table, 'table', '||c c c c||', '||c c c||', ('Extra alignment tab',)),
    # (correct_table, 'table', 'caption', 'captain', ('Undefined control sequence.', 'captain')),

    # failed unwanted commands:
    (correct_abstract, 'abstract', 'ultimate', r'ultimate \cite', (r'\cite', )),
])
def test_request_latex_with_error(correct_latex, section, replaced_value, replace_with, error_includes):
    incorrect_latex = correct_latex.replace(replaced_value, replace_with)
    check_wrong_and_right_responses(
        [f'Here is some wrong latex:\n{incorrect_latex}\nLet me know if it is ok.',
         f'Here is the correct latex:\n{correct_latex}\nShould be fine now.'],
        requester=TestLatexReviewBackgroundProductsConverser(section_names=[section],
                                                             rewind_after_end_of_review=None,
                                                             rewind_after_getting_a_valid_response=None),
        correct_value=[correct_latex],
        error_texts=error_includes)


def test_request_latex_alter_response_for_reviewer():
    requester = TestLatexReviewBackgroundProductsConverser(section_names=['abstract'],
                                                           max_reviewing_rounds=1)
    first_draft = correct_abstract.replace('ultimate', 'super ultimate')
    with OPENAI_SERVER_CALLER.mock([
            f'Here is the abstract:\n{first_draft}\n',
            'I suggest making it short',
            f'Here is the corrected shorter abstract:\n{correct_abstract}\n'],
            record_more_if_needed=False):
        assert requester.run_and_get_valid_result() == [correct_abstract]
    assert len(requester.conversation) == 3

    message_to_reviewer = requester.other_conversation[-2].content
    assert message_to_reviewer.startswith(wrap_latex(first_draft))

    # Response is reposted as fresh:
    assert requester.conversation[-1].content == wrap_latex(correct_abstract)


def test_request_latex_section_names():
    requester = TestLatexReviewBackgroundProductsConverser(section_names=['abstract'])
    assert requester.section_names == ['abstract']
    assert requester.section_name == 'abstract'
    assert requester.pretty_section_names == ['Abstract']


def test_remove_citations_from_section():
    requester = TestLatexReviewBackgroundProductsConverser(section_names=['abstract'],
                                                           un_allowed_commands=(),
                                                           should_remove_citations_from_section=True)
    abstract = r'\begin{abstract}The ultimate abstract \cite{some_citation}.\end{abstract}'
    with OPENAI_SERVER_CALLER.mock([
            f'Here is the abstract:\n{abstract}\n'],
            record_more_if_needed=False):
        assert requester.run_and_get_valid_result() == [abstract.replace(r' \cite{some_citation}', '')]


def test_rename_close_citations():
    requester = TestLatexReviewBackgroundProductsConverser(section_names=['introduction'],
                                                           un_allowed_commands=(),
                                                           should_remove_citations_from_section=False,
                                                           allowed_bibtex_citation_ids=['JONES2019AB', 'SMITH2020'],
                                                           )
    introduction = r'\section{Introduction}The ultimate introduction \cite{JONES2019, smith2020}.'
    with OPENAI_SERVER_CALLER.mock([
            f'Here is the introduction:\n{wrap_latex(introduction)}'],
            record_more_if_needed=False):

        assert requester.run_and_get_valid_result() == \
               [introduction.replace(r'JONES2019', 'JONES2019AB').replace(r'smith2020', 'SMITH2020')]


def test_check_no_additional_sections():
    requester = TestLatexReviewBackgroundProductsConverser(section_names=['introduction'])
    introduction = r'\section{Introduction}The ultimate introduction.'
    methods = r'\section{Methods}The ultimate methods.'
    introduction_and_methods = introduction + '\n' + methods
    with OPENAI_SERVER_CALLER.mock([
            f'You requested introduction but i also wrote the methods:\n{wrap_latex(introduction_and_methods)}',
            f'Now only the introduction:\n{wrap_latex(introduction)}'],
            record_more_if_needed=False):

        assert requester.run_and_get_valid_result() == [introduction]


def test_check_for_floating_citations():
    requester = TestLatexReviewBackgroundProductsConverser(section_names=['introduction'],
                                                           un_allowed_commands=(),
                                                           should_remove_citations_from_section=False,
                                                           allowed_bibtex_citation_ids=['JONES2019AB', 'SMITH2020'],
                                                           )
    introduction = r'\section{Introduction}The ultimate introduction JONES2019AB.'
    correct_introduction = introduction.replace(r'JONES2019AB', r'\cite{JONES2019AB}')
    with OPENAI_SERVER_CALLER.mock([
            f'Here is the intro, but with floating citations:\n{wrap_latex(introduction)}',
            f'Now the correct introduction:\n{wrap_latex(correct_introduction)}'],
            record_more_if_needed=False):

        assert requester.run_and_get_valid_result() == [correct_introduction]


def test_usage_of_un_allowed_commands():
    requester = TestLatexReviewBackgroundProductsConverser(section_names=['introduction'],
                                                           un_allowed_commands=(r'\verb', )
                                                           )
    introduction = r'\section{Introduction}The ultimate introduction \verb{}.'
    correct_introduction = introduction.replace(r' \verb{}', '')
    with OPENAI_SERVER_CALLER.mock([
            f'Here is the intro, but with un-allowed command:\n{wrap_latex(introduction)}',
            f'Now the correct introduction:\n{wrap_latex(correct_introduction)}'],
            record_more_if_needed=False):

        assert requester.run_and_get_valid_result() == [correct_introduction]
