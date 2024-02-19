import pickle
from dataclasses import dataclass, field
from typing import Type, Any, Dict, Optional, Tuple, Iterable

from _pytest.fixtures import fixture

from data_to_paper.base_products import DataFileDescriptions, DataFileDescription
from data_to_paper.base_steps import BaseCodeProductsGPT
from data_to_paper.research_types.scientific_research.coding_steps import ExplainCreatedDataframe, \
    RequestCodeProducts, BaseScientificCodeProductsGPT, RequestCodeExplanation
from data_to_paper.research_types.scientific_research.scientific_products import ScientificProducts
from data_to_paper.run_gpt_code.overrides.dataframes import TrackDataFrames
from data_to_paper.code_and_output_files.output_file_requirements import DataOutputFileRequirement, \
    TextContentOutputFileRequirement, OutputFileRequirements
from data_to_paper.servers.chatgpt import OPENAI_SERVER_CALLER
from tests.functional.base_steps.utils import TestProductsReviewGPT, TestAgent


@dataclass
class TestDataframeChangingCodeProductsGPT(TestProductsReviewGPT, BaseCodeProductsGPT):
    code_step = 'data_analysis'
    conversation_name: str = None
    COPY_ATTRIBUTES = BaseCodeProductsGPT.COPY_ATTRIBUTES | {'temp_dir'}
    output_file_requirements: OutputFileRequirements = OutputFileRequirements([DataOutputFileRequirement('*.csv')])
    additional_contexts: Optional[Dict[str, Any]] = field(
        default_factory=lambda: {'TrackDataFrames': TrackDataFrames(allow_dataframes_to_change_existing_series=False)})
    enforce_saving_altered_dataframes: bool = True
    code_review_prompts: Iterable[Tuple[str, bool, str]] = ()
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
class TestRequestCodeProducts(TestProductsReviewGPT, RequestCodeProducts):
    conversation_name: str = None
    code_writing_class: Type[BaseScientificCodeProductsGPT] = TestDataframeChangingCodeProductsGPT
    explain_code_class: Optional[Type[RequestCodeExplanation]] = TestRequestCodeExplanation
    explain_created_files_class: Optional[Type[ExplainCreatedDataframe]] = TestExplainCreatedDataframe
    code_step: str = 'data_analysis'
    code_name: str = 'Testing'
    temp_dir: str = None

    def get_code_writing_instance(self) -> BaseScientificCodeProductsGPT:
        cls = self.code_writing_class
        return cls.from_(self)


@fixture()
def code_running_converser(tmpdir_with_csv_file):
    return TestDataframeChangingCodeProductsGPT(
        temp_dir=tmpdir_with_csv_file,
        code_name='Testing',
        conversation_name='testing',
    )


@fixture()
def code_request_converser(tmpdir_with_csv_file, scientific_products):
    return TestRequestCodeProducts(
        products=scientific_products,
        temp_dir=tmpdir_with_csv_file)


@fixture()
def code_request_converser_without_explanation(tmpdir_with_csv_file, scientific_products):
    return TestRequestCodeProducts(
        explain_code_class=None,
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

code_creating_csv_explanation = r"""
\section{Code Explanation}
This code creates an amazing new dataframe.
"""

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


def get_code_that_creates_files(*args):
    """
    args: file1, content1, file2, content2 ...

    returns code that creates the files:

    with open('file1', 'w') as f:
        f.write('content1')
    with open('file2', 'w') as f:
        f.write('content2')
    """
    s = '\n'
    for file, content in zip(args[::2], args[1::2]):
        s += f"with open('{file}', 'w') as f:\n    f.write('{content}')\n"
    return s


def test_dataframe_tracker_is_pickleable(code_running_converser):
    pickle.dumps(code_running_converser)


def test_request_code_with_revisions(code_running_converser):
    file = 'output.txt'
    code_running_converser.code_review_prompts = (
        ('*', True, 'Output:\n{file_contents_str}\nplease list all issue.'),
    )
    code_running_converser.output_file_requirements = OutputFileRequirements(
        [TextContentOutputFileRequirement(file)])
    code1 = get_code_that_creates_files(file, "Output with mistakes")
    code2 = get_code_that_creates_files(file, "Improved output")
    code3 = get_code_that_creates_files(file, "Best output")
    with OPENAI_SERVER_CALLER.mock(
            [f'Here is my first attempt:\n```python{code1}```\n',
             '{"key issue is ...": "you must make this change ..."}',
             f'Here is the improved code:\n```python{code2}```\n',
             '{"some remaining issue ...": "we need to ..."}',
             f'Here is the best code:\n```python{code3}```\n',
             'No issues now. {}',
             ],
            record_more_if_needed=False):
        code_and_output = code_running_converser.get_code_and_output()
    assert code_and_output.code == code3
    assert code_and_output.created_files.get_single_output() == 'Best output'
    assert len(code_running_converser.conversation) == 3


def test_request_code_with_file_review_revisions(code_running_converser):
    file = 'table_?.txt'
    code_running_converser.code_review_prompts = (
        (None, True, 'Review the code.'),
        ('table_?.txt', True, 'Review {filename}\n{file_contents_str}'),
    )
    code_running_converser.output_file_requirements = OutputFileRequirements(
        [TextContentOutputFileRequirement(file)])
    code1 = get_code_that_creates_files('table_1.txt', "Output1 with mistakes", 'table_2.txt', "Output2 with mistakes")
    code2 = get_code_that_creates_files('table_1.txt', "Improved output1", 'table_2.txt', "Improved output2")
    with OPENAI_SERVER_CALLER.mock(
            [f'Here is my first attempt:\n```python{code1}```\n',
             'Code is ok {}',
             'table_1.txt is ok {}',
             'table_2.txt has errors {"key issue is ...": "please fix ..."}',
             f'Here is the improved code:\n```python{code2}```\n',
             'Code is ok {}',
             'table_1.txt is ok {}',
             'table_2.txt is ok {}',
             ],
            record_more_if_needed=False):
        code_and_output = code_running_converser.get_code_and_output()
    assert code_and_output.code == code2
    assert code_and_output.created_files.get_created_content_files_to_pretty_contents() == \
           {'table_1.txt': 'Improved output1', 'table_2.txt': 'Improved output2'}
    assert len(code_running_converser.conversation) == 3


def test_code_request_with_description_of_added_df_columns(code_request_converser_without_explanation,
                                                           scientific_products):
    with OPENAI_SERVER_CALLER.mock(
            [f'Here is the code:\n```python\n{code_reading_csv}\n```\nShould be all good.',
             new_column_dict_explanation],
            record_more_if_needed=False):
        code_request_converser_without_explanation.get_code_and_output_and_descriptions()
    for keyword in code_reading_csv_keywords_in_description:
        assert keyword in scientific_products.get_description('created_files_description:data_analysis')


def test_code_request_with_description_of_new_df(code_request_converser_without_explanation, scientific_products):
    with OPENAI_SERVER_CALLER.mock(
            [f'Here is the code:\n```python\n{code_creating_csv}\n```\nShould be all good.',
             f'Here is the description of the new file ```{new_df_explanation}```'],
            record_more_if_needed=False):
        code_request_converser_without_explanation.get_code_and_output_and_descriptions()
    for keyword in code_creating_csv_keywords_in_description:
        assert keyword in scientific_products.get_description('created_files_description:data_analysis')


def test_code_request_with_description_of_new_df_and_code_description(code_request_converser, scientific_products):
    with OPENAI_SERVER_CALLER.mock(
            [f'Here is the code:\n```python\n{code_creating_csv}\n```\nShould be all good.',
             f'Code explanation: ```{code_creating_csv_explanation}```',
             f'Here is the description of the new file ```{new_df_explanation}```',
             ],
            record_more_if_needed=False):
        code_request_converser.get_code_and_output_and_descriptions()
    for keyword in code_creating_csv_keywords_in_description:
        assert keyword in scientific_products.get_description('created_files_description:data_analysis')
