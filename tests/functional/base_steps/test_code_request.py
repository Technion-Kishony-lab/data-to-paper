from dataclasses import dataclass, field
from typing import Iterable

from _pytest.fixtures import fixture

from scientistgpt.base_steps import DataframeChangingCodeProductsGPT
from scientistgpt.conversation.actions_and_conversations import ActionsAndConversations
from scientistgpt.servers.chatgpt import OPENAI_SERVER_CALLER
from scientistgpt.utils.file_utils import run_in_directory
from tests.functional.base_steps.utils import TestAgent


@fixture()
def code_running_converser(tmpdir_with_csv_file):
    @dataclass
    class TestDataframeChangingCodeProductsGPT(DataframeChangingCodeProductsGPT):
        conversation_name: str = 'test'
        user_agent: TestAgent = TestAgent.PERFORMER
        assistant_agent: TestAgent = TestAgent.REVIEWER
        actions_and_conversations: ActionsAndConversations = field(default_factory=ActionsAndConversations)
        allowed_created_files: Iterable[str] = ('*.csv',)
        output_filename: str = None

        @property
        def data_folder(self):
            return tmpdir_with_csv_file

        @property
        def data_filenames(self):
            return ['test.csv']

    return TestDataframeChangingCodeProductsGPT()


code_reading_csv = r"""import pandas as pd
df1 = pd.read_csv('test.csv')
df1['new_column'] = df1['a'] + df1['b']
df1.to_csv('test_modified.csv')
"""

code_creating_csv = r"""import pandas as pd
df2 = pd.concat([pd.Series([1, 2, 3]), pd.Series([4, 5, 6])])
df2.to_csv('new_df.csv')
"""

code_reading_and_creating_csv = code_reading_csv + code_creating_csv


def test_request_code(code_running_converser):

    with OPENAI_SERVER_CALLER.mock([f'Python value:\n```python\n{code_reading_and_creating_csv}\n```\nShould be all good.'],
                                   record_more_if_needed=False):
        assert code_running_converser.get_analysis_code().code == code_reading_and_creating_csv
