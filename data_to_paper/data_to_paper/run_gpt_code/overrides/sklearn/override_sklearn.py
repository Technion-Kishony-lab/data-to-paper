import functools
from dataclasses import dataclass

from data_to_paper.run_gpt_code.overrides.attr_replacers import SystematicMethodReplacerContext
from sklearn.model_selection import ParameterGrid, ParameterSampler


@dataclass
class SklearnOverride(SystematicMethodReplacerContext):
    obj_import_str: str = 'sklearn'

    @property
    def obj(self):
        # TODO: add more sklearn modules. Or fix generally. See comment in SystematicAttrReplacerContext.
        from sklearn import linear_model, svm  # noqa  Needed for the import to work inclusively.
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


@dataclass
class SklearnSearchLimitCheck(SystematicMethodReplacerContext):
    base_module: object = sklearn.model_selection

    max_iterations: int = 10  # Default max iterations limit

    is_parameter_grid: bool = False
    is_parameter_sampler: bool = False

    def _should_replace(self, parent, attr_name, attr) -> bool:
        self.is_parameter_grid = issubclass(parent, ParameterGrid) and attr_name == "__len__"
        self.is_parameter_sampler = issubclass(parent, ParameterSampler) and attr_name == "__len__"
        return self.is_parameter_grid or self.is_parameter_sampler

    def _get_custom_wrapper(self, parent, attr_name, original_func):

        @functools.wraps(original_func)
        def wrapped(obj, *args, **kwargs):
            original_len = original_func(obj, *args, **kwargs)
            if original_len > self.max_iterations:
                raise RuntimeWarning(f"The total number of iterations ({original_len}) exceeds the "
                                   f"maximum allowed iterations ({self.max_iterations}). "
                                   f"Please adjust your {'parameter grid' if self.is_parameter_grid else 'n_iter'} "
                                   f"accordingly.")
            return original_len

        return wrapped
