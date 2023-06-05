from dataclasses import dataclass
from typing import Tuple, Type

from _pytest.fixtures import fixture

from scientistgpt.base_products import DataFileDescriptions, DataFileDescription
from scientistgpt.base_steps import BaseCodeProductsGPT
from scientistgpt.projects.scientific_research.coding_steps import ExplainCreatedDataframe, \
    RequestScientificCodeProducts, BaseScientificCodeProductsGPT, RequestCodeExplanation
from scientistgpt.projects.scientific_research.scientific_products import ScientificProducts
from scientistgpt.servers.chatgpt import OPENAI_SERVER_CALLER
from tests.functional.base_steps.utils import TestProductsReviewGPT, TestAgent


@dataclass
class TestDataframeChangingCodeProductsGPT(TestProductsReviewGPT, BaseCodeProductsGPT):
    conversation_name: str = None
    COPY_ATTRIBUTES = BaseCodeProductsGPT.COPY_ATTRIBUTES | {'temp_dir'}
    allowed_created_files: Tuple[str, ...] = ('*.csv',)
    allow_dataframes_to_change_existing_series: bool = False
    enforce_saving_altered_dataframes: bool = True
    offer_revision_prompt: str = None
    output_filename: str = None
    code_name: str = 'Testing'
    temp_dir: str = None

    def __post_init__(self):
        super().__post_init__()

    @property
    def data_folder(self):
        return self.temp_dir

    @property
    def data_filenames(self):
        return ['test.csv']


@dataclass
class TestExplainCreatedDataframe(ExplainCreatedDataframe):
    code_name: str = 'Testing'
    goal_noun: str = 'code explanation'
    user_agent: str = TestAgent.REVIEWER


@dataclass
class TestRequestCodeExplanation(RequestCodeExplanation):
    code_name: str = 'Testing'
    goal_noun: str = 'dataframe'
    user_agent: str = TestAgent.REVIEWER


@dataclass
class TestRequestScientificCodeProducts(TestProductsReviewGPT, RequestScientificCodeProducts):
    conversation_name: str = None
    EXPLAIN_CODE_CLASS = TestRequestCodeExplanation
    EXPLAIN_CREATED_FILES_CLASS = TestExplainCreatedDataframe
    code_step: str = 'data_analysis'
    code_name: str = 'Testing'
    temp_dir: str = None

    @property
    def code_writing_class(self) -> Type[BaseScientificCodeProductsGPT]:
        return TestDataframeChangingCodeProductsGPT


@fixture()
def code_running_converser(tmpdir_with_csv_file):
    return TestDataframeChangingCodeProductsGPT(temp_dir=tmpdir_with_csv_file)


@fixture()
def code_request_converser(tmpdir_with_csv_file, scientific_products):
    return TestRequestScientificCodeProducts(
        products=scientific_products,
        temp_dir=tmpdir_with_csv_file)


@fixture()
def scientific_products(tmpdir_with_csv_file):
    scientific_products = ScientificProducts()
    scientific_products.data_file_descriptions = DataFileDescriptions(
        [DataFileDescription(file_path='test.csv', description='test file')], data_folder=tmpdir_with_csv_file)
    return scientific_products


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

code_creating_csv_explanation = "\nThis code creates an amazing new dataframe"

code_creating_csv_keywords_in_description = ('new_df.csv', 'col1', 'col2', 'col3')

new_df_explanation = "\nThis file is a new dataframe which has the following columns:\na b c\n"

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


def test_code_request_with_description_of_added_df_columns(code_request_converser, scientific_products):
    with OPENAI_SERVER_CALLER.mock(
            [f'Here is the code:\n```python\n{code_reading_csv}\n```\nShould be all good.',
             new_column_dict_explanation],
            record_more_if_needed=False):
        code_request_converser.get_code_and_output_and_add_file_descriptions_and_code_explanation(
            with_code_explanation=False)
    for keyword in code_reading_csv_keywords_in_description:
        assert keyword in scientific_products.get_description('created_files_description:data_analysis')


def test_code_request_with_description_of_new_df(code_request_converser, scientific_products):
    with OPENAI_SERVER_CALLER.mock(
            [f'Here is the code:\n```python\n{code_creating_csv}\n```\nShould be all good.',
             f'Here is the description of the new file ```{new_df_explanation}```'],
            record_more_if_needed=False):
        code_request_converser.get_code_and_output_and_add_file_descriptions_and_code_explanation(
            with_code_explanation=False)
    for keyword in code_creating_csv_keywords_in_description:
        assert keyword in scientific_products.get_description('created_files_description:data_analysis')


def test_code_request_with_description_of_new_df_and_code_description(code_request_converser, scientific_products):
    with OPENAI_SERVER_CALLER.mock(
            [f'Here is the code:\n```python\n{code_creating_csv}\n```\nShould be all good.',
             f'Here is the description of the new file ```{new_df_explanation}```',
             f'Code explanation: ```{code_creating_csv_explanation}```',],
            record_more_if_needed=False):
        code_request_converser.get_code_and_output_and_add_file_descriptions_and_code_explanation()
    for keyword in code_creating_csv_keywords_in_description:
        assert keyword in scientific_products.get_description('created_files_description:data_analysis')
