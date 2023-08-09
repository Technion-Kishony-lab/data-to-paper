from contextlib import contextmanager
from typing import List

import pandas as pd
import statsmodels.api

from .pvalue_dtype import PValueDtype

DEFAULT_STAT_CLASSES = ['api.OLS', 'api.WLS', 'api.GLS', 'genmod.generalized_linear_model.GLM']


@contextmanager
def label_pvalues(stat_classes: List[str] = None):
    """
    A context manager that patches the pvalues attribute of the given stat classes to be of type PValueDtype.
    """
    stat_classes = stat_classes or DEFAULT_STAT_CLASSES
    original_fits = {}

    def custom_fit(self, *args, **kwargs):
        # Call the original fit method
        result = original_fits[self.__class__](self, *args, **kwargs)
        # Patch the pvalues attribute
        try:
            if isinstance(result.pvalues, pd.Series):
                result.pvalues = result.pvalues.astype(PValueDtype(self.__class__.__name__))
        except (AttributeError, TypeError, ValueError):
            pass
        return result

    # Backup the original fit methods and replace with custom_fit
    for stat_class in stat_classes:
        module = statsmodels
        for submodule in stat_class.split('.'):
            module = getattr(module, submodule)
        cls = module
        original_fits[cls] = cls.fit
        cls.fit = custom_fit

    yield

    # Restore the original fit methods
    for cls, original_fit in original_fits.items():
        cls.fit = original_fit
