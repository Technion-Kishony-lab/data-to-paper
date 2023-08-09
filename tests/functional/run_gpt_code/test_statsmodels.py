import statsmodels.api as sm
import pandas as pd
from statsmodels.genmod.generalized_linear_model import GLM

from data_to_paper.run_gpt_code.overrides.statsmodels.override_statsmodels_fit import label_pvalues, PValueDtype


def test_label_pvalues():
    with label_pvalues():
        # Example data
        data = sm.datasets.longley.load()
        X = sm.add_constant(data.exog)
        y = data.endog

        models = [
            (sm.OLS(y, X), 'OLS'),
            (sm.WLS(y, X), 'WLS'),
            (sm.GLS(y, X), 'GLS'),
            (GLM(y, X), 'GLM'),
        ]

        for model, func in models:
            results = model.fit()
            assert results.pvalues.dtype == PValueDtype(func)


def test_df_describe_under_label_pvalues():
    df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    with label_pvalues():
        df.describe()
