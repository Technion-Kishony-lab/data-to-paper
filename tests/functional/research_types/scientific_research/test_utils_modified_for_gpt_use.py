import pandas as pd
import pytest
from _pytest.fixtures import fixture
from _pytest.python_api import raises

from data_to_paper.research_types.scientific_research.utils_for_gpt_code.utils_modified_for_gpt_use. \
    check_df_of_table import check_df_of_table_for_content_issues
from data_to_paper.research_types.scientific_research.utils_for_gpt_code. \
    utils_modified_for_gpt_use.to_latex_with_note import _check_for_table_style_issues
from data_to_paper.research_types.scientific_research.utils_for_gpt_code.\
    utils_modified_for_gpt_use.to_pickle import get_dataframe_to_pickle_attr_replacer
from data_to_paper.run_gpt_code.overrides.pvalue import PValue, is_p_value
from data_to_paper.run_gpt_code.types import RunUtilsError
from data_to_paper.utils.file_utils import run_in_directory


@fixture()
def df():
    return pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]}, index=['x', 'y', 'z'])


def test_to_pickle_with_checks_runs_ok(tmpdir, df):
    with run_in_directory(tmpdir):
        with get_dataframe_to_pickle_attr_replacer():
            df.to_pickle('test.csv')
            df2 = pd.read_pickle('test.csv')
            assert df.equals(df2)


def test_to_pickle_with_checks_with_pvalue_runs_ok(tmpdir, df):
    with run_in_directory(tmpdir):
        with get_dataframe_to_pickle_attr_replacer():
            # assign PValue to a cell:
            df.iloc[1, 0] = PValue(0.1)
            df.to_pickle('test.csv')
            df2 = pd.read_pickle('test.csv')
            assert df.equals(df2)
            assert is_p_value(df2['a'][1])


def test_to_pickle_with_checks_does_not_allow_wrong_arguments(df):
    with get_dataframe_to_pickle_attr_replacer():
        with raises(RunUtilsError):
            df.to_pickle(None)


def test_check_for_table_style_issues_runs_ok(df):
    _check_for_table_style_issues(df, 'test.tex')


def test_check_for_table_style_issues_runs_ok_on_df_with_list():
    df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, [5], 6]})
    _check_for_table_style_issues(df, 'test.tex')


def test_check_df_of_table_for_content_issues_runs_ok(df):
    issues = check_df_of_table_for_content_issues(df, 'table_1.pkl', prior_tables={})
    assert not issues


def test_check_df_of_table_for_content_issues_raises_on_nan(df):
    df.iloc[0, 1] = float('nan')
    issues = check_df_of_table_for_content_issues(df, 'table_1.pkl', prior_tables={})
    assert len(issues) == 1
    assert 'NaN' in issues[0].category
    assert 'has a NaN value' in issues[0].issue


def test_check_df_of_table_for_content_issues_raises_on_p_value_of_nan(df):
    df.iloc[0, 1] = PValue(float('nan'))
    issues = check_df_of_table_for_content_issues(df, 'table_1.pkl', prior_tables={})
    assert len(issues) == 1
    assert 'NaN' in issues[0].category
    assert 'has a NaN value' in issues[0].issue


@pytest.mark.skip(reason='Test for repeated values is disabled. High risk of false positive in small datasets')
def test_check_df_of_table_for_content_issues_with_repeated_value(df):
    df.iloc[0, 0] = 2 / 7
    df.iloc[1, 1] = 2 / 7
    issues = check_df_of_table_for_content_issues(df, 'table_1.pkl', prior_tables={})
    assert len(issues) == 1
    assert 'overlap' in issues[0].category
    assert '(0, 0), (1, 1)' in issues[0].issue


def test_check_df_of_table_for_content_issues_with_repeated_value_in_prior_table(df):
    prior_table = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]}, index=['x', 'y', 'z'])
    prior_table.iloc[0, 0] = 2 / 7
    df.iloc[1, 1] = 2 / 7
    issues = check_df_of_table_for_content_issues(df, 'table_1.pkl', prior_tables={'table_0.pkl': prior_table})
    assert len(issues) == 1
    assert 'overlap' in issues[0].category
    assert 'table_0.pkl' in issues[0].issue
