import functools
import warnings

import sklearn

from data_to_paper.run_gpt_code.overrides.attr_replacers import method_replacer


def sklearn_override():
    """
    A context manager that prevents calling a fit function of a skylearn instance more than once.
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
            return result
        wrapped.is_wrapped = True
        return wrapped

    return method_replacer(sklearn, fit_wrapper, should_replace_func)
