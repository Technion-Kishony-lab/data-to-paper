import pandas as pd
import pytest
from pytest import fixture

from data_to_paper.research_types.hypothesis_testing.check_df_to_funcs.df_checker import DfContentChecker, \
    AnnotationDfChecker, TableDfContentChecker, FigureDfContentChecker
from data_to_paper.run_gpt_code.overrides.pvalue import PValue


@fixture()
def df():
    return pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]}, index=['x', 'y', 'z'])


def test_check_for_table_style_issues_runs_ok(df):
    AnnotationDfChecker(df=df, filename='test').run_checks()


def test_check_for_table_style_issues_runs_ok_on_df_with_list():
    df = pd.DataFrame({'Open': [1, 2, 3], 'Closed': [4, [5], 6]})
    issues = AnnotationDfChecker(df=df, filename='df_tag', kwargs=dict(caption='caption')).run_checks()[0]
    assert not issues


def test_check_df_of_table_for_content_issues_runs_ok(df):
    issues = DfContentChecker(df=df, filename='df_tag').run_checks()[0]
    assert not issues


def test_check_df_of_table_for_content_issues_raises_on_nan(df):
    df.iloc[0, 1] = float('nan')
    issues = DfContentChecker(df=df, filename='df_tag', prior_dfs={}).run_checks()[0]
    assert len(issues) == 1
    assert 'has 1 NaN value' in issues[0].issue


def test_check_df_of_table_for_content_issues_raises_on_p_value_of_nan(df):
    df.iloc[0, 1] = PValue(float('nan'))
    issues = DfContentChecker(df=df, filename='df_tag').run_checks()[0]
    assert len(issues) == 1
    assert 'has 1 NaN value' in issues[0].issue


def test_check_df_of_table_for_content_issues_with_repeated_value(df):
    df.iloc[0, 0] = 2 / 7
    df.iloc[1, 1] = 2 / 7
    issues = TableDfContentChecker(df=df, filename='df_tag').run_checks()[0]
    assert len(issues) == 1
    assert 'Overlapping' in issues[0].category
    assert '(0, 0), (1, 1)' in issues[0].issue


def test_check_df_of_table_for_content_issues_with_repeated_value_in_prior_table(df):
    prior_table = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]}, index=['x', 'y', 'z'])
    prior_table.iloc[0, 0] = 2 / 7
    df.iloc[1, 1] = 2 / 7
    issues = TableDfContentChecker(df=df, filename='df_tag', prior_dfs={'df_other': prior_table}).run_checks()[0]
    assert len(issues) == 1
    assert 'Overlapping' in issues[0].category
    assert 'df_other' in issues[0].issue


def test_check_df_of_table_for_header_issues(df):
    df.columns = [('a', 'b'), 'x']
    issues = FigureDfContentChecker(df=df, filename='df_tag',
                                    kwargs={'y': ['x']}).run_checks()[0]
    assert len(issues) == 1
    assert 'tuple' in issues[0].issue
