from dataclasses import dataclass, field

import pytest
from _pytest.fixtures import fixture

from data_to_paper.base_steps.debugger import DebuggerConverser
from data_to_paper.conversation.actions_and_conversations import ActionsAndConversations
from data_to_paper.servers.chatgpt import OPENAI_SERVER_CALLER

from .utils import TestAgent


@dataclass
class TestDebuggerGPT(DebuggerConverser):
    conversation_name: str = 'test'
    user_agent: TestAgent = TestAgent.PERFORMER
    assistant_agent: TestAgent = TestAgent.REVIEWER
    actions_and_conversations: ActionsAndConversations = field(default_factory=ActionsAndConversations)
    output_filename: str = 'test_output.txt'
    data_files: tuple = ('test.csv',)
    enforce_saving_altered_dataframes: bool = True


@fixture()
def debugger(tmpdir_with_csv_file):
    return TestDebuggerGPT(data_folder=tmpdir_with_csv_file)


code_creating_file_correctly = r"""```python
with open('test_output.txt', 'w') as f:
    f.write('The answer is 42')
```
"""

code_altering_dataframe = r"""```python
import pandas as pd
df1 = pd.read_csv('test.csv')
df1['new_column'] = df1['a'] + df1['b']
df1.to_csv('test_modified.csv')
with open('test_output.txt', 'w') as f:
    f.write('The answer is 42')
```"""


def test_debugger_run_and_get_outputs(debugger):
    with OPENAI_SERVER_CALLER.mock([f'Here is the correct code:\n{code_creating_file_correctly}\nShould be all good.'],
                                   record_more_if_needed=False):
        assert debugger.run_debugging().output == 'The answer is 42'


@pytest.mark.parametrize('correct_code, replaced_value, replace_with, error_includes', [
    (code_creating_file_correctly, 'f.write', 'f.write(', ['SyntaxError']),
])
def test_request_code_with_error(correct_code, replaced_value, replace_with, error_includes, debugger):
    incorrect_code = correct_code.replace(replaced_value, replace_with)
    with OPENAI_SERVER_CALLER.mock([f'Here is a wrong code:\n{incorrect_code}\nLet me know what is wrong with it.',
                                    f'Here is the correct code:\n{correct_code}\nShould be fine now.'
                                    ],
                                   record_more_if_needed=False):
        code_and_output = debugger.run_debugging()
        assert code_and_output.output == 'The answer is 42'
        error_message = debugger.conversation[2]
        for error_include in error_includes:
            assert error_include in error_message.content
