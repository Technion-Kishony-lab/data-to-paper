from dataclasses import dataclass

import pytest

from scientistgpt.base_steps import LatexReviewBackgroundProductsConverser
from scientistgpt.servers.chatgpt import OPENAI_SERVER_CALLER

from .utils import TestProductsReviewGPT, check_wrong_and_right_responses


@dataclass
class TestLatexReviewBackgroundProductsConverser(TestProductsReviewGPT, LatexReviewBackgroundProductsConverser):
    keep_intermediate_files_in_debug: bool = False
    max_reviewing_rounds: int = 0


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
    (correct_table, 'table'),
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
    (correct_table, 'table', r'\begin{table}', r'\begin', (r'Failed to extract table from response',)),
    (correct_title, 'title', '}', '', (r'Failed to extract title from response',)),

    # failed compilations:
    (correct_table, 'table', '||c c c c||', '||c c c||', ('Extra alignment tab',)),
    (correct_table, 'table', 'caption', 'captain', ('Undefined control sequence.', 'captain')),

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
    with OPENAI_SERVER_CALLER.mock([
            f'Here is the abstract:\n{correct_abstract.replace("ultimate", "super ultimate")}\n',
            'I suggest making it short',
            f'Here is the corrected shorter abstract:\n{correct_abstract}\n'],
            record_more_if_needed=False):
        assert requester.run_dialog_and_get_valid_result() == [correct_abstract]
    assert len(requester.conversation) == 3

    # Response is sent to reviewer with latex triple backticks:
    message_to_reviewer = requester.other_conversation[-2].content
    assert 'Here is the abstract:\n```latex' in message_to_reviewer

    # Response is reposted as fresh:
    assert requester.conversation[-1].content == correct_abstract


def test_request_latex_section_names():
    requester = TestLatexReviewBackgroundProductsConverser(section_names=['abstract'])
    assert requester.section_names == ['abstract']
    assert requester.section_name == 'abstract'
    assert requester.pretty_section_names == ['Abstract']
