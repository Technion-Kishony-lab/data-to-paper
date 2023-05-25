from dataclasses import dataclass, field

import pytest

from scientistgpt.base_steps import BaseLatexProductsReviewGPT
from scientistgpt.base_steps.debugger_gpt import DebuggerGPT
from scientistgpt.conversation.actions_and_conversations import ActionsAndConversations
from scientistgpt.servers.chatgpt import OPENAI_SERVER_CALLER

from .utils import TestAgent


@dataclass
class TestDebuggerGPT(DebuggerGPT):
    conversation_name: str = 'test'
    user_agent: TestAgent = TestAgent.PERFORMER
    assistant_agent: TestAgent = TestAgent.REVIEWER
    actions_and_conversations: ActionsAndConversations = field(default_factory=ActionsAndConversations)
    output_filename: str = 'test_output.txt'


code_creating_file_correctly = r"""```python
with open('test_output.txt', 'w') as f:
    f.write('The answer is 42')
```
"""


def test_debugger_run_and_get_outputs():
    with OPENAI_SERVER_CALLER.mock([f'Here is the correct code:\n{code_creating_file_correctly}\nShould be all good.'],
                                   record_more_if_needed=False):
        assert TestDebuggerGPT().run_debugging().output == 'The answer is 42'


@pytest.mark.parametrize('correct_code, replaced_value, replace_with, error_includes', [
    (code_creating_file_correctly, 'f.write', 'f.write(', ['SyntaxError']),
    (code_creating_file_correctly, 'test_output', 'wrong_file', ['test_output']),
])
def test_request_latex_with_error(correct_code, replaced_value, replace_with, error_includes):
    incorrect_code = correct_code.replace(replaced_value, replace_with)
    with OPENAI_SERVER_CALLER.mock([f'Here is an wrong code:\n{incorrect_code}\nLet me know what is wrong with it.',
                                    f'Here is the correct code:\n{correct_code}\nShould be fine now.'
                                    ],
                                   record_more_if_needed=False):
        debugger = TestDebuggerGPT()
        code_and_output = debugger.run_debugging()
        assert code_and_output.output == 'The answer is 42'
        error_message = debugger.conversation[2]
        print(error_message.content)
        for error_include in error_includes:
            assert error_include in error_message.content
