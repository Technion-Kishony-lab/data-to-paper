import pytest
import statsmodels.api as sm
import pandas as pd
from _pytest.fixtures import fixture
from scipy.stats import stats
from scipy import stats as scipy_stats
from scipy.stats._stats_py import TtestResult
from statsmodels.genmod.generalized_linear_model import GLM
from statsmodels.stats.anova import anova_lm

from data_to_paper.run_gpt_code.code_runner import CodeRunner
from data_to_paper.run_gpt_code.overrides.contexts import OverrideStatisticsPackages
from data_to_paper.run_gpt_code.overrides.sklearn.override_sklearn import SklearnFitOverride
from data_to_paper.run_gpt_code.overrides.statsmodels.override_statsmodels import StatsmodelsFitPValueOverride
from data_to_paper.run_gpt_code.overrides.scipy.override_scipy import ScipyPValueOverride
from data_to_paper.run_gpt_code.overrides.pvalue import PValue, is_p_value
from statsmodels.formula.api import ols, logit

from data_to_paper.run_gpt_code.run_issues import RunIssue


@fixture()
def data_for_ttest():
    return (
        [1, 2, 3, 4, 5],
        [6, 7, 8, 9, 10],
    )


@fixture()
def data_y_x():
    return pd.DataFrame({'y': [0, 0, 1, 1, 1], 'x': [1, 2, 3, 4, 5]})


@fixture()
def data_Logit(data_y_x):
    x = data_y_x['x']
    x = sm.add_constant(x)
    y = data_y_x['y']
    return y, x


@fixture()
def data_chi2_contingency():
    return [[10, 10, 20], [20, 20, 20]]


def test_fit_results_do_not_allow_summary(data_y_x):
    with OverrideStatisticsPackages():
        model = ols('y ~ x', data=data_y_x)
        results = model.fit()
        with pytest.raises(RunIssue) as e:
            results.summary()
        assert 'Do not use the `summary` function of statsmodels.' in str(e.value)


@pytest.mark.parametrize('func', [
    sm.OLS,
    sm.WLS,
    sm.GLS,
    GLM,
])
def test_statsmodels_label_pvalues(func):
    with StatsmodelsFitPValueOverride() as context:
        # Example data
        data = sm.datasets.longley.load()
        X = sm.add_constant(data.exog)
        y = data.endog
        model = func(y, X)
        results = model.fit()
        pval = results.pvalues[0]
        assert is_p_value(pval)
        assert pval.created_by == func.__name__
        assert context.pvalue_creating_funcs == [func.__name__]
        if hasattr(results, 'summary2'):
            s2 = results.summary2()
            table1 = s2.tables[1]
            attr = 'P>|t|' if 't' in table1.columns else 'P>|z|'
            pval = s2.tables[1][attr][0]
            assert is_p_value(pval)
            assert pval.created_by == func.__name__


@pytest.mark.parametrize('with_redundant_feature', [True, False])
def test_statsmodels_issues_on_singular_matrix(with_redundant_feature):
    with OverrideStatisticsPackages() as context:
        # Example data
        data = pd.DataFrame({'sex': ['M', 'M', 'F', 'F', 'F'] * 100, 'y': [1, 2, 3, 4, 5] * 100})
        data = pd.get_dummies(data)
        formula = 'y ~ sex_M'
        if with_redundant_feature:
            formula += ' + sex_F'
        ols(data=data, formula=formula).fit()
    if with_redundant_feature:
        assert len(context.issues) == 1
        assert 'eigenvalues' in context.issues[0].issue
    else:
        assert len(context.issues) == 0


def test_statsmodels_logit(data_Logit):
    with StatsmodelsFitPValueOverride():
        model = sm.Logit(*data_Logit)
        results = model.fit()

        pval = results.pvalues[0]
        assert is_p_value(pval)
        assert pval.created_by == 'Logit'


@pytest.mark.parametrize('calling_fit', [
    True,
    False,
])
def test_statsmodels_create_issue_if_no_fit_is_called(calling_fit, data_Logit):
    with OverrideStatisticsPackages() as context:
        model = sm.Logit(*data_Logit)
        if calling_fit:
            model.fit()
    if calling_fit:
        assert len(context.issues) == 0
    else:
        assert len(context.issues) == 1


def test_statsmodels_anova_lm(data_y_x):
    with OverrideStatisticsPackages():
        model = ols('y ~ x', data=data_y_x).fit()
        anova_result = anova_lm(model, typ=2)
        pval = anova_result.loc['x', 'PR(>F)']
        assert is_p_value(pval)


def test_statsmodels_multicomp():
    from statsmodels.stats.multicomp import pairwise_tukeyhsd
    with OverrideStatisticsPackages():
        tukey = pairwise_tukeyhsd(endog=[1, 2, 3, 4, 5], groups=[1, 1, 2, 2, 2], alpha=0.05)
    assert is_p_value(tukey.summary().data[1][3])
    assert is_p_value(tukey.summary()[1][3].data)
    assert is_p_value(tukey.pvalues[0])


def test_statsmodels_logit_func(data_y_x):
    with StatsmodelsFitPValueOverride():
        results = logit('y ~ x', data=data_y_x).fit()
        table2 = results.summary2().tables[1].iloc[:, 0:4]
        table2.columns = ['coef', 'std err', 'z', 'P>|z|']
        P = table2['P>|z|']
        with pytest.raises(RunIssue):
            P.astype(float)


def test_statsmodels_ols():
    with StatsmodelsFitPValueOverride():
        # Example of using the ols function, not the class
        data = sm.datasets.longley.load().data
        results = ols('TOTEMP ~ GNPDEFL', data=data).fit()
        pval = results.pvalues[0]
        assert is_p_value(pval)


def test_sklean_raise_on_multiple_fit_calls():

    with SklearnFitOverride():
        # Example data
        data = sm.datasets.longley.load()
        X = sm.add_constant(data.exog)
        y = data.endog
        from sklearn.linear_model import LinearRegression
        model = LinearRegression()
        model.fit(X, y)
        with pytest.raises(RunIssue):
            model.fit(X, y)


response_with_two_fit_calls = """
```
from sklearn.linear_model import LinearRegression
import statsmodels.api as sm
data = sm.datasets.longley.load()
X = sm.add_constant(data.exog)
y = data.endog
model = LinearRegression()
model.fit(X, y)
model.fit(X, y)
```
"""


def test_sklean_raise_on_multiple_fit_calls_in_code_runner():
    _, _, _, exception = CodeRunner(response=response_with_two_fit_calls,
                                    additional_contexts={'OverrideStatisticsPackages': OverrideStatisticsPackages()},
                                    allowed_read_files=None,
                                    ).run_code_in_separate_process()
    assert isinstance(exception, RunIssue)


code0 = """
```from statsmodels.formula.api import logit
import pandas as pd
df = pd.DataFrame({'Y': [1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
                   'X': [1, 0, 1, 0, 1, 0, 1, 0, 1, 0],})
table1_model = logit("interaction ~ Beauty", data=df).fit()
```
"""


def test_run_code_with_none_serializable_exception():
    runner = CodeRunner(response=code0, allowed_read_files=None)
    _, _, _, exception = runner.run_code_in_separate_process()
    assert exception.get_type_name() == 'PatsyError'


def test_sklean_do_not_raise_on_single_fit_call_in_code_runner():
    response_with_single_fit_calls = response_with_two_fit_calls.replace('model.fit(X, y)\n```', '```')
    _, _, _, exception = CodeRunner(response=response_with_single_fit_calls,
                                    additional_contexts={'OverrideStatisticsPackages': OverrideStatisticsPackages()},
                                    allowed_read_files=None,
                                    ).run_code_in_separate_process()
    assert exception is None


def test_df_describe_under_label_pvalues():
    df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    with StatsmodelsFitPValueOverride():
        df.describe()


def test_scipy_label_pvalues():
    with ScipyPValueOverride():
        # Example data
        data = [2.5, 3.1, 2.8, 3.2, 3.0]
        popmean = 3.0
        result = stats.ttest_1samp(data, popmean)
        p_value = result.pvalue
        assert is_p_value(p_value)
        assert p_value.created_by == 'ttest_1samp'


def test_scipy_label_pvalues_raise_on_nan():
    with ScipyPValueOverride():
        data = []
        popmean = 3.0
        with pytest.raises(RunIssue):
            t_statistic, p_value = stats.ttest_1samp(data, popmean)


def test_scipy_label_pvalues_chi2_contingency(data_chi2_contingency):
    with ScipyPValueOverride():
        p_value = scipy_stats.chi2_contingency(data_chi2_contingency).pvalue
        assert is_p_value(p_value)


def test_scipy_label_pvalues_ttest_ind(data_for_ttest):
    with ScipyPValueOverride():
        # Example data
        p_value = scipy_stats.ttest_ind(*data_for_ttest).pvalue
        assert is_p_value(p_value)
        assert p_value.created_by == 'ttest_ind'


@pytest.mark.skip()
def test_scipy_stats_t_sf():
    # test stats.t.sf
    with ScipyPValueOverride():
        # Example data
        t_statistic = 3.0
        df = 10
        p_value = scipy_stats.t.sf(t_statistic, df)
        assert is_p_value(p_value)


def test_pvalue_from_dict():
    ttest_results = {'HighBP': TtestResult(statistic=5., pvalue=PValue(0.7), df=3534,
                                           estimate=1, standard_error=1, alternative=1)}
    df = pd.DataFrame.from_dict(ttest_results, orient='index')
    pvalue = df['pvalue'][0]
    assert is_p_value(pvalue)


def test_do_not_allow_unpacking_and_getitem_of_ttest_ind(data_for_ttest):
    # Sanity:
    result = scipy_stats.ttest_ind(*data_for_ttest)
    statistic, pvalue = result
    assert result.statistic == statistic
    assert result.pvalue == pvalue
    assert len(result) == 2
    assert result[0] == statistic
    assert result[1] == pvalue

    with ScipyPValueOverride(prevent_unpacking=True):
        result = scipy_stats.ttest_ind(*data_for_ttest)
        # allowed:
        result.pvalue
        assert len(result) == 2
        # not allowed:
        with pytest.raises(RunIssue) as e:
            statistic, pvalue = result
        assert 'Unpacking' in str(e.value)
        with pytest.raises(RunIssue) as e:
            result[0]
        assert 'by index' in str(e.value)


def test_do_not_allow_unpacking_and_getitem_of_chi2_contingency(data_chi2_contingency):
    # Sanity:
    result = scipy_stats.chi2_contingency(data_chi2_contingency)
    statistic, pvalue, dof, expected_freq = result
    assert result.statistic == statistic
    assert result.pvalue == pvalue
    assert len(result) == 4
    assert result[0] == statistic
    assert result[1] == pvalue
    with ScipyPValueOverride(prevent_unpacking=True):
        result = scipy_stats.chi2_contingency(data_chi2_contingency)
        # allowed:
        result.pvalue
        assert len(result) == 4
        # not allowed:
        with pytest.raises(RunIssue) as e:
            statistic, pvalue, dof, expected_freq = result
        assert 'Unpacking' in str(e.value)
        with pytest.raises(RunIssue) as e:
            result[0]
        assert 'by index' in str(e.value)
