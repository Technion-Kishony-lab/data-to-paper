import pytest
import statsmodels.api as sm
import pandas as pd
from scipy.stats import stats
from scipy import stats as scipy_stats
from scipy.stats._stats_py import TtestResult
from statsmodels.genmod.generalized_linear_model import GLM

from data_to_paper.run_gpt_code.overrides.sklearn.override_sklearn import SklearnOverride
from data_to_paper.run_gpt_code.overrides.statsmodels.override_statsmodels import StatsmodelsOverride
from data_to_paper.run_gpt_code.overrides.scipy.override_scipy import ScipyOverride
from data_to_paper.run_gpt_code.overrides.types import PValue, is_p_value
from statsmodels.formula.api import ols, logit


@pytest.mark.parametrize('func', [
    sm.OLS,
    sm.WLS,
    sm.GLS,
    GLM,
])
def test_statsmodels_label_pvalues(func):
    with StatsmodelsOverride():
        # Example data
        data = sm.datasets.longley.load()
        X = sm.add_constant(data.exog)
        y = data.endog
        model = func(y, X)
        results = model.fit()
        pval = results.pvalues[0]
        assert is_p_value(pval)
        assert pval.created_by == func.__name__
        if hasattr(results, 'summary2'):
            s2 = results.summary2()
            table1 = s2.tables[1]
            attr = 'P>|t|' if 't' in table1.columns else 'P>|z|'
            pval = s2.tables[1][attr][0]
            assert is_p_value(pval)
            assert pval.created_by == func.__name__


def test_statsmodels_logit():
    with StatsmodelsOverride():
        # Example data
        X = [1, 2, 3, 4, 5]
        y = [0, 0, 1, 1, 1]
        X = sm.add_constant(X)

        model = sm.Logit(y, X)
        results = model.fit()

        pval = results.pvalues[0]
        assert is_p_value(pval)
        assert pval.created_by == 'Logit'


def test_statsmodels_logit_func():
    with StatsmodelsOverride():
        # Example data
        X = [1, 2, 3, 4, 5]
        y = [0, 0, 1, 1, 1]

        results = logit('y ~ X', data=pd.DataFrame({'y': y, 'X': X})).fit()
        table2 = results.summary2().tables[1].iloc[:, 0:4]
        table2.columns = ['coef', 'std err', 'z', 'P>|z|']
        P = table2['P>|z|']
        with pytest.raises(ValueError):
            P.astype(float)


def test_statsmodels_ols():
    with StatsmodelsOverride():
        # Example of using the ols function, not the class
        data = sm.datasets.longley.load().data
        results = ols('TOTEMP ~ GNPDEFL', data=data).fit()
        pval = results.pvalues[0]
        assert is_p_value(pval)


def test_sklean_raise_on_multiple_fit_calls():
    from sklearn.linear_model import LinearRegression
    with SklearnOverride():
        # Example data
        data = sm.datasets.longley.load()
        X = sm.add_constant(data.exog)
        y = data.endog
        model = LinearRegression()
        model.fit(X, y)
        with pytest.raises(RuntimeWarning):
            model.fit(X, y)


def test_df_describe_under_label_pvalues():
    df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    with StatsmodelsOverride():
        df.describe()


def test_scipy_label_pvalues():
    with ScipyOverride():
        # Example data
        data = [2.5, 3.1, 2.8, 3.2, 3.0]
        popmean = 3.0
        t_statistic, p_value = stats.ttest_1samp(data, popmean)
        assert is_p_value(p_value)
        assert p_value.created_by == 'ttest_1samp'


@pytest.mark.skip()
def test_scipy_stats_t_sf():
    # test stats.t.sf
    with ScipyOverride():
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
