from dataclasses import dataclass, field

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
\end{table}"""

incorrect_table = correct_table.replace(r'\begin{tabular}{||c c c c||}', r'\begin{tabular}{||c c c|}')


def test_request_latex():
    with OPENAI_SERVER_CALLER.mock([f'Here is the table:\n{correct_table}\nLet me know if it is ok.'],
                                   record_more_if_needed=False):
        assert TestBaseLatexProductsReviewGPT(section_names=['table']).get_section() == correct_table


def test_request_latex_with_wrong_latex():
    with OPENAI_SERVER_CALLER.mock([f'Here is a wrong table:\n{incorrect_table}\nLet me know if it is ok.',
                                    f'Here is a correct table:\n{correct_table}\nLet me know if it is ok.'
                                    ],
                                   record_more_if_needed=False):
        assert TestBaseLatexProductsReviewGPT(section_names=['table']).get_section() == correct_table
