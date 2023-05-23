from dataclasses import dataclass, field

import pytest

from scientistgpt.base_steps import BaseLatexProductsReviewGPT
from scientistgpt.conversation.actions_and_conversations import ActionsAndConversations
from scientistgpt.servers.chatgpt import OPENAI_SERVER_CALLER

from .utils import TestAgent


@dataclass
class TestBaseLatexProductsReviewGPT(BaseLatexProductsReviewGPT):
    conversation_name: str = 'test'
    user_agent: TestAgent = TestAgent.PERFORMER
    assistant_agent: TestAgent = TestAgent.REVIEWER
    actions_and_conversations: ActionsAndConversations = field(default_factory=ActionsAndConversations)
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
    with OPENAI_SERVER_CALLER.mock([f'Here is the correct latex:\n{correct_latex}\nShould be all good.'],
                                   record_more_if_needed=False):
        assert TestBaseLatexProductsReviewGPT(section_names=[section]).get_section() == correct_latex


@pytest.mark.parametrize('correct_latex, section, replaced_value, replace_with, corrected', [
    (correct_title, 'title', 'The ultimate', 'The & ultimate', r'The \& ultimate'),
])
def test_request_latex_autocorrect(correct_latex, section, replaced_value, replace_with, corrected):
    incorrect_latex = correct_latex.replace(replaced_value, replace_with)
    corrected_latex = incorrect_latex.replace(replace_with, corrected)
    with OPENAI_SERVER_CALLER.mock([f'Here is some wrong latex:\n{incorrect_latex}\nYou should correct it yourself.',
                                    ],
                                   record_more_if_needed=False):
        latex_requester = TestBaseLatexProductsReviewGPT(section_names=[section])
        assert latex_requester.get_section() == corrected_latex


@pytest.mark.parametrize('correct_latex, section, replaced_value, replace_with, error_includes', [
    # failed extractions:
    (correct_table, 'table', r'\begin{table}', r'\begin', (r'Failed to extract table from response',)),
    (correct_title, 'title', '}', '', (r'Failed to extract title from response',)),

    # failed compilations:
    (correct_table, 'table', '||c c c c||', '||c c c||', ('Extra alignment tab',)),
    (correct_table, 'table', 'caption', 'captain', ('Undefined control sequence.', 'captain')),
])
def test_request_latex_with_error(correct_latex, section, replaced_value, replace_with, error_includes):
    incorrect_latex = correct_latex.replace(replaced_value, replace_with)
    with OPENAI_SERVER_CALLER.mock([f'Here is some wrong latex:\n{incorrect_latex}\nLet me know if it is ok.',
                                    f'Here is the correct latex:\n{correct_latex}\nShould be fine now.'
                                    ],
                                   record_more_if_needed=False):
        latex_requester = TestBaseLatexProductsReviewGPT(section_names=[section])
        assert latex_requester.get_section() == correct_latex
        error_message = latex_requester.conversation[4]
        for error_include in error_includes:
            assert error_include in error_message.content
