from dataclasses import dataclass, field
from unittest import mock

import pytest
from pytest import fixture

from data_to_paper.base_steps.debugger import DebuggerConverser
from data_to_paper.conversation.actions_and_conversations import ActionsAndConversations
from data_to_paper.code_and_output_files.output_file_requirements import TextContentOutputFileRequirement, \
    OutputFileRequirements
from data_to_paper.run_gpt_code.base_run_contexts import MultiRunContext
from data_to_paper.run_gpt_code.code_runner import CodeRunner
from data_to_paper.run_gpt_code.run_issues import RunIssue, CodeProblem
from data_to_paper.servers.llm_call import OPENAI_SERVER_CALLER

from .utils import TestAgent


@dataclass
class TestDebuggerGPT(DebuggerConverser):
    conversation_name: str = 'test'
    user_agent: TestAgent = TestAgent.PERFORMER
    assistant_agent: TestAgent = TestAgent.REVIEWER
    actions_and_conversations: ActionsAndConversations = field(default_factory=ActionsAndConversations)
    data_filenames: tuple = ()


class TestCodeRunnerWithForgive(CodeRunner):
    def run(self, code: str, *args, **kwargs):
        context = MultiRunContext()
        if 'Small problem' in code:
            context.issues = [RunIssue(issue='Small problem that can be forgiven',
                                       code_problem=CodeProblem.OutputFileAnnotation,
                                       forgive_after=1)]
        else:
            context.issues = [RunIssue(issue='Big problem that cannot be forgiven',
                                       code_problem=CodeProblem.OutputFileAnnotation,
                                       forgive_after=None)]
        return None, [], context, None


class TestCodeRunnerWithoutForgive(TestCodeRunnerWithForgive):
    forgive_after = None


@fixture()
def debugger(tmpdir_with_csv_file):
    return TestDebuggerGPT(data_folder=tmpdir_with_csv_file,
                           output_file_requirements=OutputFileRequirements(
                               [TextContentOutputFileRequirement('test_output.txt')]),
                           data_filenames=('test.csv',),)


@fixture()
def debugger_with_timeout(tmpdir_with_csv_file):
    return TestDebuggerGPT(timeout_sec=3)


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

code_runs_for_more_than_1_second = r"""```python
import time
time.sleep(5)
```"""


code_runs_for_less_than_1_second = r"""```python
import time
time.sleep(0.5)
```"""


code_with_small_problem = r"""```python
# Small problem
```"""


code_with_big_problem = r"""```python
# Big problem
```"""


def test_debugger_run_and_get_outputs(debugger):
    with OPENAI_SERVER_CALLER.mock([f'Here is the correct code:\n{code_creating_file_correctly}\nShould be all good.'],
                                   record_more_if_needed=False):
        assert debugger.run_debugging().created_files.get_created_content_files_to_contents()['test_output.txt'] == \
               'The answer is 42'


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
        assert code_and_output.created_files.get_created_content_files_to_contents()['test_output.txt'] == \
               'The answer is 42'
        error_message = debugger.conversation[2]
        for error_include in error_includes:
            assert error_include in error_message.content


def test_code_with_timeout(debugger_with_timeout):
    with OPENAI_SERVER_CALLER.mock([code_runs_for_more_than_1_second,
                                    code_runs_for_less_than_1_second],
                                   record_more_if_needed=False):
        debugger_with_timeout.run_debugging()


@pytest.mark.parametrize('codes', [
    [code_with_small_problem, code_with_small_problem],
    [code_with_small_problem, code_with_big_problem, code_with_small_problem],
])
def test_debugger_forgives_small_problems(debugger, codes):
    with OPENAI_SERVER_CALLER.mock(codes, record_more_if_needed=False):
        debugger.code_runner_cls = TestCodeRunnerWithForgive
        debugger.run_debugging()
