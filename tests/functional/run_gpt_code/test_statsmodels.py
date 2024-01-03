import pytest
import statsmodels.api as sm
import pandas as pd
from scipy.stats import stats
from scipy import stats as scipy_stats
from scipy.stats._stats_py import TtestResult, PearsonRResult
from statsmodels.genmod.generalized_linear_model import GLM
from statsmodels.stats.anova import anova_lm

from data_to_paper.run_gpt_code.code_runner import CodeRunner
from data_to_paper.run_gpt_code.exceptions import FailedRunningCode
from data_to_paper.run_gpt_code.overrides.contexts import OverrideStatisticsPackages
from data_to_paper.run_gpt_code.overrides.sklearn.override_sklearn import SklearnFitOverride
from data_to_paper.run_gpt_code.overrides.statsmodels.override_statsmodels import StatsmodelsFitPValueOverride
from data_to_paper.run_gpt_code.overrides.scipy.override_scipy import ScipyPValueOverride, ScipyTtestResultOverride
from data_to_paper.run_gpt_code.overrides.pvalue import PValue, is_p_value
from statsmodels.formula.api import ols, logit

from data_to_paper.run_gpt_code.run_issues import RunIssue


def test_fit_results_do_not_allow_summary():
    with OverrideStatisticsPackages():
        data = pd.DataFrame({'y': [1, 2, 3, 4, 5], 'x': [1, 2, 3, 4, 5]})
        model = ols('y ~ x', data=data)
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


def test_statsmodels_logit():
    with StatsmodelsFitPValueOverride():
        # Example data
        X = [1, 2, 3, 4, 5]
        y = [0, 0, 1, 1, 1]
        X = sm.add_constant(X)

        model = sm.Logit(y, X)
        results = model.fit()

        pval = results.pvalues[0]
        assert is_p_value(pval)
        assert pval.created_by == 'Logit'


@pytest.mark.parametrize('calling_fit', [
    True,
    False,
])
def test_statsmodels_create_issue_if_no_fit_is_called(calling_fit):
    with OverrideStatisticsPackages() as context:
        # Example data
        X = [1, 2, 3, 4, 5]
        y = [0, 0, 1, 1, 1]
        X = sm.add_constant(X)
        model = sm.Logit(y, X)
        if calling_fit:
            model.fit()
    if calling_fit:
        assert len(context.issues) == 0
    else:
        assert len(context.issues) == 1


def test_statsmodels_anova_lm():
    with OverrideStatisticsPackages():
        data = pd.DataFrame({'y': [1, 2, 3, 4, 5], 'x': [1, 2, 3, 4, 5]})
        model = ols('y ~ x', data=data).fit()
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


def test_statsmodels_logit_func():
    with StatsmodelsFitPValueOverride():
        # Example data
        X = [1, 2, 3, 4, 5]
        y = [0, 0, 1, 1, 1]

        results = logit('y ~ X', data=pd.DataFrame({'y': y, 'X': X})).fit()
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
        t_statistic, p_value = stats.ttest_1samp(data, popmean)
        assert is_p_value(p_value)
        assert p_value.created_by == 'ttest_1samp'


def test_scipy_label_pvalues_raise_on_nan():
    with ScipyPValueOverride():
        data = []
        popmean = 3.0
        with pytest.raises(RunIssue):
            t_statistic, p_value = stats.ttest_1samp(data, popmean)


def test_scipy_label_pvalues_chi2_contingency():
    with ScipyPValueOverride():
        # Example data
        observed = [[10, 10, 20], [20, 20, 20]]
        chi2, p, dof, expected = scipy_stats.chi2_contingency(observed)
        assert is_p_value(p)


def test_scipy_label_pvalues_ttest_ind():
    with ScipyPValueOverride():
        # Example data
        data1 = [0, 1, 2, 3, 4, 5]
        data2 = [5, 6, 7, 8, 9, 10]
        t_statistic, p_value = scipy_stats.ttest_ind(data1, data2)
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


def test_TtestResult_unpacking():
    with ScipyTtestResultOverride():
        ttest_results = TtestResult(statistic=5., pvalue=0.7, df=3534,
                                    estimate=1, standard_error=1, alternative=1)
        # Explicitly accessing the attributes is allowed:
        assert ttest_results.statistic == 5.
        assert ttest_results.pvalue == 0.7
        with pytest.raises(RunIssue) as e:
            # Unpacking is not allowed:
            statistic, pvalue = ttest_results
        assert 'Unpacking' in str(e.value)


def test_PearsonRResult_unpacking():
    # Sanity check:
    pearson_results = PearsonRResult(pvalue=0.7, statistic=1, alternative=1, n=1, x=1, y=1)
    statistic, pvalue = pearson_results
    assert statistic == 1
    assert pvalue == 0.7

    with ScipyTtestResultOverride():
        pearson_results = PearsonRResult(pvalue=0.7, statistic=1, alternative=1, n=1, x=1, y=1)
        # Explicitly accessing the attributes is allowed:
        assert pearson_results.statistic == 1
        assert pearson_results.pvalue == 0.7
        with pytest.raises(RunIssue) as e:
            # Unpacking is not allowed:
            statistic, pvalue = pearson_results
        assert 'Unpacking' in str(e.value)
