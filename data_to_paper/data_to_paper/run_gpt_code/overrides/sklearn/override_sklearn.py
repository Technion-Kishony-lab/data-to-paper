import functools
from dataclasses import dataclass

from data_to_paper.run_gpt_code.overrides.attr_replacers import SystematicMethodReplacerContext


@dataclass
class SklearnOverride(SystematicMethodReplacerContext):
    obj_import_str: str = 'sklearn'

    @property
    def obj(self):
        from sklearn import linear_model
        import sklearn
        return sklearn

    def _should_replace(self, parent, attr_name, attr) -> bool:
        return attr_name.startswith('fit')

    def _get_custom_wrapper(self, parent, attr_name, original_func):

        @functools.wraps(original_func)
        def wrapped(obj, *args, **kwargs):
            result = original_func(obj, *args, **kwargs)
            if self._is_called_from_data_to_paper():
                if hasattr(obj, '_prior_fit_results') and obj._prior_fit_results is result:
                    raise RuntimeWarning(
                        f"The `{original_func.__name__}` function was already called on this object. "
                        f"Multiple calls should be avoided as the same result instance is returned again.")
                obj._prior_fit_results = result

            return result

        return wrapped
