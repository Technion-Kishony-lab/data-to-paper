import functools
import inspect
from dataclasses import dataclass
from typing import Iterable, Optional

from data_to_paper.env import TRACK_P_VALUES
from data_to_paper.run_gpt_code.attr_replacers import SystematicFuncReplacerContext

from ..pvalue import convert_to_p_value, TrackPValueCreationFuncs
from ..types import is_namedtuple, NoIterTuple
from ..utils import get_func_call_str


@dataclass
class ScipyPValueOverride(SystematicFuncReplacerContext, TrackPValueCreationFuncs):
    prevent_unpacking: Optional[bool] = True  # False - do not prevent;  True - prevent;  None - create issues
    package_names: Iterable[str] = ('scipy', )
    obj_import_str: str = 'scipy'

    def _should_replace(self, module, func_name, func) -> bool:
        doc = inspect.getdoc(func)
        if doc and "p-value" in doc:
            return True
        return False

    def _get_custom_wrapper(self, parent, attr_name, original_func):

        @functools.wraps(original_func)
        def wrapped(*args, **kwargs):
            result = original_func(*args, **kwargs)
            created_by = original_func.__name__

            if TRACK_P_VALUES:
                # Get function call string representation:
                # For each arg in args, get a short representation of it, like 'array(shape=(2, 3))':
                func_call_str = get_func_call_str(created_by, args, kwargs)
                # Replace the pvalues attribute if it exists
                try:
                    asdict = {k.strip('_'): v for k, v in result._asdict().items()}
                    if 'pvalue' in asdict:
                        asdict['pvalue'] = convert_to_p_value(asdict['pvalue'],
                                                              created_by=created_by,
                                                              func_call_str=func_call_str)
                        self._add_pvalue_creating_func(created_by)
                        result = type(result)(**asdict)
                except (AttributeError, TypeError, ValueError):
                    pass

            if self.prevent_unpacking is not False and is_namedtuple(result):
                result = NoIterTuple(result, created_by=created_by, context=self,
                                     should_raise=self.prevent_unpacking is True,
                                     should_record=self.prevent_unpacking is None)

            return result

        return wrapped
