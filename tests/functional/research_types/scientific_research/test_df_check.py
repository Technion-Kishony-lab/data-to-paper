import pytest

from data_to_paper.research_types.hypothesis_testing.check_df_to_funcs.df_checker import BaseChecker, \
    create_and_run_chain_checker, SyntaxDfChecker


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
