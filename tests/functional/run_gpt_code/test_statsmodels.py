import pytest
import statsmodels.api as sm
import pandas as pd
from scipy.stats import stats
from scipy.stats._stats_py import TtestResult
from statsmodels.genmod.generalized_linear_model import GLM

from data_to_paper.run_gpt_code.overrides.statsmodels.override_statsmodels import statsmodels_override
from data_to_paper.run_gpt_code.overrides.statsmodels.pvalue_dtype import PValueFloat
from data_to_paper.run_gpt_code.overrides.scipy.override_scipy import scipy_override
from data_to_paper.run_gpt_code.overrides.types import PValue
from statsmodels.formula.api import ols

@pytest.mark.parametrize('func', [
    sm.OLS,
    sm.WLS,
    sm.GLS,
    GLM,
])
def test_statsmodels_label_pvalues(func):
    with statsmodels_override():
        # Example data
        data = sm.datasets.longley.load()
        X = sm.add_constant(data.exog)
        y = data.endog
        model = func(y, X)
        results = model.fit()
        pval = results.pvalues[0]
        assert isinstance(pval, PValue)
        assert pval.created_by == func.__name__
        if hasattr(results, 'summary2'):
            s2 = results.summary2()
            table1 = s2.tables[1]
            attr = 'P>|t|' if 't' in table1.columns else 'P>|z|'
            pval = s2.tables[1][attr][0]
            assert isinstance(pval, PValue)
            assert pval.created_by == func.__name__


def test_statsmodels_logit():
    with statsmodels_override():
        # Example data
        data = {
            'X': [1, 2, 3, 4, 5],
            'Y': [0, 0, 1, 1, 1]
        }
        df = pd.DataFrame(data)

        # Split into features and target
        X = df['X']
        y = df['Y']

        # Add a constant to the predictor variables (it's a requirement for statsmodels)
        X = sm.add_constant(X)

        # Fit the logistic regression model
        model = sm.Logit(y, X)
        results = model.fit()

        pval = results.pvalues[0]
        assert isinstance(pval, PValue)
        assert pval.created_by == 'Logit'


def test_statsmodels_ols():
    with statsmodels_override():
        # Example of using the ols function, not the class
        data = sm.datasets.longley.load().data
        results = ols('TOTEMP ~ GNPDEFL', data=data).fit()
        pval = results.pvalues[0]
        assert isinstance(pval, PValue)


def test_df_describe_under_label_pvalues():
    df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    with statsmodels_override():
        df.describe()


def test_scipy_label_pvalues():
    with scipy_override():
        # Example data
        data = [2.5, 3.1, 2.8, 3.2, 3.0]
        popmean = 3.0
        t_statistic, p_value = stats.ttest_1samp(data, popmean)
        assert type(p_value) == PValue
        assert p_value.created_by == 'ttest_1samp'


def test_pvalue_from_dict():
    ttest_results = {'HighBP': TtestResult(statistic=5., pvalue=PValue(0.7), df=3534,
                                           estimate=1, standard_error=1, alternative=1)}
    df = pd.DataFrame.from_dict(ttest_results, orient='index')
    pvalue = df['pvalue'][0]
    assert isinstance(pvalue, PValue)
