import functools
from dataclasses import dataclass

import sklearn

from data_to_paper.run_gpt_code.overrides.attr_replacers import SystematicMethodReplacerContext


@dataclass
class SklearnOverride(SystematicMethodReplacerContext):
    base_module: object = sklearn

    def _should_replace(self, parent, attr_name, attr) -> bool:
        return attr_name.startswith('fit')

    def _get_custom_wrapper(self, parent, attr_name, original_func):

        @functools.wraps(original_func)
        def wrapped(obj, *args, **kwargs):
            if self._is_called_from_data_to_paper():
                if getattr(obj, '_fit_was_called', False):
                    raise RuntimeWarning(f"The `{original_func.__name__}` function was already called on this object.")
                obj._fit_was_called = True

            return original_func(obj, *args, **kwargs)

        return wrapped
