import functools
import inspect
from dataclasses import dataclass
from typing import Iterable

from data_to_paper.env import TRACK_P_VALUES
from data_to_paper.run_gpt_code.overrides.attr_replacers import SystematicFuncReplacerContext, \
    SystematicMethodReplacerContext, MultiAttrReplacerContext
from data_to_paper.utils.text_formatting import short_repr

from ..pvalue import convert_to_p_value, TrackPValueCreationFuncs
from ...run_issues import CodeProblem, RunIssue


@dataclass
class ScipyPValueOverride(SystematicFuncReplacerContext, TrackPValueCreationFuncs):
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

            if TRACK_P_VALUES:
                # Get function call string representation:
                # For each arg in args, get a short representation of it, like 'array(shape=(2, 3))':
                func_call_str = original_func.__name__ + '(' + ', '.join(
                    [short_repr(arg) for arg in args] + [f'{k}={short_repr(v)}' for k, v in kwargs.items()]) + ')'
                # Replace the pvalues attribute if it exists
                try:
                    asdict = {k.strip('_'): v for k, v in result._asdict().items()}
                    if 'pvalue' in asdict:
                        created_by = original_func.__name__
                        asdict['pvalue'] = convert_to_p_value(asdict['pvalue'],
                                                              created_by=created_by,
                                                              func_call_str=func_call_str)
                        self._add_pvalue_creating_func(created_by)
                        result = type(result)(**asdict)
                except (AttributeError, TypeError, ValueError):
                    pass
            return result

        return wrapped


@dataclass
class ScipyTtestResultOverride(MultiAttrReplacerContext):
    """
    Prevent iteration over the TtestResult and PearsonRResult objects, which are namedtuples.
    In particular, this prevents unpacking of the objects, which can lead to mistakes in the order of the values.
    """
    def _get_all_parents(self) -> list:
        from scipy.stats._stats_py import TtestResult, PearsonRResult
        return [TtestResult, PearsonRResult]

    def _get_all_attrs_for_parent(self, parent) -> Iterable[str]:
        return ['__iter__']

    def _get_custom_wrapper(self, parent, attr_name, original_func):
        def __iter__(self):
            obj_name = parent.__name__
            raise RunIssue.from_current_tb(
                code_problem=CodeProblem.NonBreakingRuntimeIssue,
                issue=f'Unpacking, or otherwise iterating over, the {obj_name} object can lead to mistakes.',
                instructions='Your code should instead explicitly access the attributes of the {obj_name} object.'
            )
        return __iter__
