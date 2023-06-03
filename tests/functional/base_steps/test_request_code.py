from dataclasses import dataclass, field
from typing import Tuple

from _pytest.fixtures import fixture

from scientistgpt.base_steps import DataframeChangingCodeProductsGPT
from scientistgpt.base_products import DataFileDescriptions, DataFileDescription
from scientistgpt.conversation.actions_and_conversations import ActionsAndConversations
from scientistgpt.projects.scientific_research.scientific_products import ScientificProducts
from scientistgpt.servers.chatgpt import OPENAI_SERVER_CALLER
from tests.functional.base_steps.utils import TestAgent, TestProductsReviewGPT


@dataclass
class TestDataframeChangingCodeProductsGPT(TestProductsReviewGPT, DataframeChangingCodeProductsGPT):
    allowed_created_files: Tuple[str] = ('*.csv',)
    output_filename: str = None
    code_name: str = 'Testing'
    temp_dir: str = None

    @property
    def data_folder(self):
        return self.temp_dir

    @property
    def data_filenames(self):
        return ['test.csv']


@fixture()
def code_running_converser(tmpdir_with_csv_file):
    return TestDataframeChangingCodeProductsGPT(temp_dir=tmpdir_with_csv_file)


code_reading_csv = r"""import pandas as pd
df1 = pd.read_csv('test.csv')
df1['new_column'] = df1['a'] + df1['b']
df1.to_csv('test_modified.csv')
"""

code_reading_csv_keywords_in_description = ('test_modified.csv', 'test.csv', 'new_column')

code_creating_csv = r"""import pandas as pd
df2 = pd.DataFrame([["n", "e", "w"], ["r", "o", "w"]], columns=['col1', 'col2', 'col3'])
df2.to_csv('new_df.csv')
"""

code_creating_csv_keywords_in_description = ('new_df.csv', 'col1', 'col2', 'col3')

new_df_explanation = "This file is a new dataframe which has the following columns:\na b c"

code_reading_not_changing_existing_series = r"""import pandas as pd
import copy
df1 = pd.read_csv('test.csv')
df2 = copy.copy(df1)
assert df2.is_overridden()
df2['new_column'] = df2['a'] + df2['b']
"""

new_column_dict_explanation = """
the column explanation is:
{
    'new_column': 'this is just a new column',
}
"""


def test_request_code_with_adding_new_column(code_running_converser):
    with OPENAI_SERVER_CALLER.mock(
            [f'Python value:\n```python\n{code_reading_csv}\n```\nShould be all good.',
             new_column_dict_explanation],
            record_more_if_needed=False):
        codee_and_outputs = {"data_preprocessing": code_running_converser.get_code_and_output()}
        scientific_products = ScientificProducts()
        scientific_products.data_file_descriptions = DataFileDescriptions(
            [DataFileDescription(file_path='test.csv', description='test file')])
        scientific_products.codes_and_outputs = codee_and_outputs
        for keyword in code_reading_csv_keywords_in_description:
            assert keyword in scientific_products.get_description('created_files_description:data_preprocessing')


def test_request_code_with_creating_new_df(code_running_converser):
    with OPENAI_SERVER_CALLER.mock(
            [f'Python value:\n```python\n{code_creating_csv}\n```\nShould be all good.',
             new_df_explanation],
            record_more_if_needed=False):
        code_and_outputs = {"data_preprocessing": code_running_converser.get_code_and_output()}
        scientific_products = ScientificProducts()
        scientific_products.codes_and_outputs = code_and_outputs
        for keyword in code_creating_csv_keywords_in_description:
            assert keyword in scientific_products.get_description('created_files_description:data_preprocessing')
