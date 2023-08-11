import functools
import warnings

import numpy as np
import pandas as pd
import statsmodels.api

# from .pvalue_dtype import PValueDtype
from ..attr_replacers import method_replacer
from ..types import PValue, convert_to_p_value


def _get_summary2_func(self, original_func):
    """
    Get the summary2 function of a statsmodels class.
    """

    def custom_summary2(*args, **kwargs):
        """
        A custom summary2 function that replaces the pvalues attribute of the summary tables with a PValueDtype.
        Replaces "P>|t|" and "P>|z|" with PValueDtype.
        """
        result = original_func(self, *args, **kwargs)

        tables = result.tables
        table1 = tables[1]

        pval_names = [name for name in table1.columns if name.startswith('P>')]
        for pval_name in pval_names:
            # table1[pval_name] = table1[pval_name].astype(PValueDtype(self.__class__.__name__))
            table1[pval_name] = table1[pval_name].apply(functools.partial(PValue.from_value,
                                                                          created_by=self.__class__.__name__))
        return result

    return custom_summary2


def statsmodels_override():
    """
    A context manager that replaces the pvalues attribute of all fit functions in statsmodels with a
    PValueDtype.
    """
    def should_replace_func(obj, attr_name):
        return attr_name.startswith('fit')

    def fit_wrapper(original_func):
        @functools.wraps(original_func)
        def wrapped(self, *args, **kwargs):
            if getattr(self, '_fit_was_called', False):
                raise RuntimeWarning("The fit function was already called on this object.")
            result = original_func(self, *args, **kwargs)
            self._fit_was_called = True

            # Replace the pvalues attribute if it exists
            # result.pvalues = result.pvalues.astype(PValueDtype(self.__class__.__name__))
            for attr in ['pvalues', 'f_pvalue', 'pvalue']:
                if not hasattr(result, attr):
                    continue
                pvalues = getattr(result, attr)
                pvalues = convert_to_p_value(pvalues, created_by=self.__class__.__name__)
                try:
                    setattr(result, attr, pvalues)
                except AttributeError:
                    if attr in getattr(result, '_cache', {}):
                        result._cache[attr] = pvalues
                        
            if hasattr(result, 'summary2'):
                original_summary2 = result.summary2
                result.summary2 = _get_summary2_func(self, original_summary2)
            return result
        wrapped.is_wrapped = True
        return wrapped

    return method_replacer(statsmodels, fit_wrapper, should_replace_func)
