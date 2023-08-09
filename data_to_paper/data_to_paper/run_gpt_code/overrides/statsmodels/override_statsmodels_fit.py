import functools

import statsmodels.api

from .pvalue_dtype import PValueDtype
from ..attr_replacers import method_replacer


def label_pvalues():
    """
    A context manager that replaces the pvalues attribute of all fit functions in statsmodels with a
    PValueDtype.
    """
    def should_replace_func(obj, attr_name):
        return attr_name.startswith('fit')

    def fit_wrapper(original_func):
        @functools.wraps(original_func)
        def wrapped(self, *args, **kwargs):
            result = original_func(self, *args, **kwargs)

            # Replace the pvalues attribute if it exists
            try:
                result.pvalues = result.pvalues.astype(PValueDtype(self.__class__.__name__))
            except (AttributeError, TypeError, ValueError):
                pass
            return result
        wrapped.is_wrapped = True
        return wrapped

    return method_replacer(statsmodels, fit_wrapper, should_replace_func)
