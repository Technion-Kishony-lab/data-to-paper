import pytest
import statsmodels.api as sm
import pandas as pd
from scipy.stats import stats
from statsmodels.genmod.generalized_linear_model import GLM

from data_to_paper.run_gpt_code.overrides.statsmodels.override_statsmodels import statsmodels_label_pvalues, PValueDtype
from data_to_paper.run_gpt_code.overrides.statsmodels.pvalue_dtype import PValueFloat
from data_to_paper.run_gpt_code.overrides.scipy.override_scipy import scipy_label_pvalues


@pytest.mark.parametrize('func', [
    sm.OLS,
    sm.WLS,
    sm.GLS,
    GLM,
])
def test_statsmodels_label_pvalues(func):
    with statsmodels_label_pvalues():
        # Example data
        data = sm.datasets.longley.load()
        X = sm.add_constant(data.exog)
        y = data.endog
        model = func(y, X)
        results = model.fit()
        assert results.pvalues.dtype == PValueDtype(func.__name__)
        if hasattr(results, 'summary2'):
            s2 = results.summary2()
            table1 = s2.tables[1]
            attr = 'P>|t|' if 't' in table1.columns else 'P>|z|'
            assert s2.tables[1][attr].dtype == PValueDtype(func.__name__)


def test_df_describe_under_label_pvalues():
    df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    with statsmodels_label_pvalues():
        df.describe()


def test_scipy_label_pvalues():
    with scipy_label_pvalues():
        # Example data
        data = [2.5, 3.1, 2.8, 3.2, 3.0]
        popmean = 3.0
        t_statistic, p_value = stats.ttest_1samp(data, popmean)
        assert type(p_value) == PValueFloat

