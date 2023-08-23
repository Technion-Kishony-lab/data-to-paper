import pandas as pd
from _pytest.python_api import raises

from data_to_paper.researches_types.scientific_research.utils_for_gpt_code.utils_modified_for_gpt_use.to_latex_with_note import \
    _check_for_table_style_issues
from data_to_paper.researches_types.scientific_research.utils_for_gpt_code.utils_modified_for_gpt_use.to_pickle import \
    get_dataframe_to_pickle_attr_replacer
from data_to_paper.run_gpt_code.overrides.types import PValue
from data_to_paper.run_gpt_code.types import RunUtilsError
from data_to_paper.utils.file_utils import run_in_directory


def test_to_pickle_with_checks_runs_ok(tmpdir):
    with run_in_directory(tmpdir):
        with get_dataframe_to_pickle_attr_replacer():
            df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
            df.to_pickle('test.csv')
            df2 = pd.read_pickle('test.csv')
            assert df.equals(df2)


def test_to_pickle_with_checks_with_pvalue_runs_ok(tmpdir):
    with run_in_directory(tmpdir):
        with get_dataframe_to_pickle_attr_replacer():
            df = pd.DataFrame({'a': [1, PValue(0.5), 3], 'b': [4, 5, 6]})
            df.to_pickle('test.csv')
            df2 = pd.read_pickle('test.csv')
            assert df.equals(df2)
            assert isinstance(df2['a'][1], PValue)


def test_to_pickle_with_checks_does_not_allow_wrong_arguments():
    with get_dataframe_to_pickle_attr_replacer():
        df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
        with raises(RunUtilsError):
            df.to_pickle(None)


def test_check_for_table_style_issues_runs_ok():
    df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    _check_for_table_style_issues(df, 'test.tex')


def test_check_for_table_style_issues_runs_ok_on_df_with_list():
    df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, [5], 6]})
    _check_for_table_style_issues(df, 'test.tex')
