import numpy as np
import pandas as pd
import pytest

from data_to_paper.research_types.hypothesis_testing.check_df_to_funcs.df_checker import BaseChecker, \
    create_and_run_chain_checker, SyntaxDfChecker, check_analysis_df, check_displayitem_df
from data_to_paper.research_types.hypothesis_testing.coding.analysis.my_utils.df_to_figure import analysis_df_to_figure
from data_to_paper.research_types.hypothesis_testing.coding.analysis.my_utils.df_to_latex import analysis_df_to_latex
from data_to_paper.research_types.hypothesis_testing.coding.displayitems.my_utils.df_to_figure import \
    displayitems_df_to_figure
from data_to_paper.research_types.hypothesis_testing.coding.displayitems.my_utils.df_to_latex import \
    displayitems_df_to_latex
from tests.functional.research_types.scientific_research.utils import simulate_save_load


def test_BaseChecker_raises_if_not_all_check_methods_are_selected():
    class TestChecker(BaseChecker):
        def check_1(self):
            pass

        def check_2(self):
            pass

        CHOICE_OF_CHECKS = {check_2: True}

    test_checker = TestChecker()
    try:
        test_checker.run_checks()
    except AssertionError as e:
        assert 'check_1' in str(e)


@pytest.mark.parametrize('stop_after_first_issue', [True, False])
def test_BaseChecker_accumulates_issues(stop_after_first_issue):
    class TestChecker(BaseChecker):
        def check_1(self):
            self._append_issue(issue='issue 1')

        def check_2(self):
            self._append_issue(issue='issue 2')

        CHOICE_OF_CHECKS = {check_1: True, check_2: True}

    test_checker = TestChecker(stop_after_first_issue=stop_after_first_issue)
    issues, _ = test_checker.run_checks()
    assert len(issues) == 1 if stop_after_first_issue else 2


@pytest.mark.parametrize('stop_after_first_issue', [True, False])
def test_ChainChecker_runs_all_checkers(stop_after_first_issue):
    class TestChecker(BaseChecker):
        def check_1(self):
            self._append_issue(issue='issue 1')

    class TestChecker2(BaseChecker):
        def check_2(self):
            self._append_issue(issue='issue 2')

    issues, _ = create_and_run_chain_checker([TestChecker, TestChecker2], stop_after_first_issue=stop_after_first_issue)
    assert len(issues) == 1 if stop_after_first_issue else 2


def test_ChainChecker_transfer_intermediate_results():
    class TestChecker(BaseChecker):
        def check_1(self):
            self._append_issue(issue='issue 1')
            self.intermediate_results['result_1'] = 1

    class TestChecker2(BaseChecker):
        def check_2(self):
            self._append_issue(issue='issue 2')
            self.intermediate_results['result_2'] = 2

    issues, intermediate_results = create_and_run_chain_checker([TestChecker, TestChecker2],
                                                                stop_after_first_issue=False)
    assert len(issues) == 2
    assert intermediate_results == {'result_1': 1, 'result_2': 2}


"""SyntaxDfChecker"""


@pytest.mark.parametrize('filename, legitimate', [
    ('df_table', True),
    ('df_ta?ble', False),
    ('df_table_formatted', True),
    ('df_table.pkl', False),
])
def test_SyntaxDfChecker_filename(filename, legitimate):
    checker = SyntaxDfChecker(filename=filename)
    checker.check_filename()
    issues = checker.issues
    if legitimate:
        assert not issues
    else:
        assert len(issues) == 1
        assert filename in issues[0].issue


@pytest.mark.parametrize('label', [None, 'label'])
def test_SyntaxDfChecker_no_label(label):
    checkers = SyntaxDfChecker(filename='df_table', kwargs={'label': label})
    checkers.check_no_label()
    issues = checkers.issues
    if label:
        assert len(issues) == 1
        assert 'label' in issues[0].issue
    else:
        assert not issues


DF = pd.DataFrame


class MyType:
    pass


def _check_issues(df, check_func, expected_words_in_issues, **k):
    issues = check_func(df, **k)
    print(f'\n\nFor data frame:\n{df}\nIssues:\n{issues.get_message_and_comment()[0]}\n')
    assert len(issues) == len(expected_words_in_issues)
    for issue, expected_words in zip(issues, expected_words_in_issues):
        if isinstance(expected_words, str):
            expected_words = [expected_words]
        for expected_word in expected_words:
            assert expected_word in str(issue)


@pytest.mark.parametrize('df, kwargs, expected_words_in_issues', [
    (DF({'a': [1, 3, 2, 7, 8, 4]}, index=['a', 'b', 'c', 'd', 'e', 'f']),
     dict(), []),
    (DF({'a': [DF({'b': [1, 2, 3]})]}),
     dict(), ['Something wierd in your dataframe']),
    (DF({'a': [[1, 2], {'k': 7}]}),
     dict(), [("values of types", 'dict', 'list')]),
    (DF({'a': [1., np.nan], 'b': [1, 2]}),
     dict(), ['NaN']),
    (DF({MyType(): [1, 2]}),
     dict(), [('headers of unsupported types', 'MyType')]),
    (DF({'a': [1, 3, 2, 7, 8, 4], 'b': [1, 2, 3, 4, 5, 6]}).describe(),
     dict(), ['df.describe']),
    (DF({'a': [1, 3, 5, 2]}),
     dict(), [('just a range', 'from 0 to 3')]),
    (DF({'c': [103.7, 103.7], 'd': [1, 3]}),
     dict(), [('same values in multiple cells', '103.7')]),
    (DF({'a': np.linspace(0, 6, 100)}, index=np.linspace(10, 16, 100)),
     dict(), [('Too large df', '100 rows')]),
])
def test_analysis_df_to_latex_checks(df, kwargs, expected_words_in_issues):
    df = simulate_save_load(analysis_df_to_latex, df, 'df_tag', **kwargs)
    _check_issues(df, check_analysis_df, expected_words_in_issues)


@pytest.mark.parametrize('df, kwargs, expected_words_in_issues', [
    (DF({'a': [1, 3, 2, 7, 8, 4]}),
     dict(y='a', kind='bar'), []),
    (DF({'a': np.linspace(0, 6, 100)}),
     dict(y='a', kind='bar'), ['100 bars']),
    (DF({'a': ['kuk', 'kuki']}),
     dict(y='a', kind='bar'), ['not numeric']),
])
def test_analysis_df_to_figure_checks(df, kwargs, expected_words_in_issues):
    df = simulate_save_load(analysis_df_to_figure, df, 'df_tag', **kwargs)
    _check_issues(df, check_analysis_df, expected_words_in_issues)
# TODO: add more tests. see FigureDfContentChecker


@pytest.mark.parametrize('df, kwargs, expected_words_in_issues', [
    (DF({'Apple': [1, 3, 2, 7]}, index=['1', '2', '3', '4']),
     dict(caption='Caption'), []),
    (DF({'Apple': [1, 3, 2, 7]}, index=['1', '2', '3', '4']),
     dict(), ['caption']),
])
def test_displayitems_df_to_latex_checks(df, kwargs, expected_words_in_issues):
    df = simulate_save_load(analysis_df_to_latex, df, 'df_tag', **kwargs)
    df = simulate_save_load(displayitems_df_to_latex, df, 'df_tag_formatted', **kwargs)
    _check_issues(df, check_displayitem_df, expected_words_in_issues,
                  compilation_func=lambda _, __: 0.4)
# TODO: add more tests. see TableSecondContentChecker, TableCompilationDfContentChecker,
#  AnnotationDfChecker,


@pytest.mark.parametrize('df, kwargs, expected_words_in_issues', [
    (DF({'Apple': [1, 3, 2, 7, 8, 4]}),
     dict(y='Apple', kind='bar', caption='Caption'), []),
    (DF({'Apple': [1, 3, 2, 7, 8, 4]}),
     dict(y='Apple', kind='bar'), ['caption']),
])
def test_displayitems_df_to_figure_checks(tmpdir, df, kwargs, expected_words_in_issues):
    df = simulate_save_load(analysis_df_to_figure, df, 'df_tag', **kwargs)
    df = simulate_save_load(displayitems_df_to_figure, df, 'df_tag_formatted', **kwargs)
    _check_issues(df, check_displayitem_df, expected_words_in_issues,
                  output_folder=tmpdir)
# TODO: add more tests. see SecondFigureContentChecker, FigureAnnotationDfChecker,
