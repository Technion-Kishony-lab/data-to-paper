import numbers
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Iterable, Optional, Tuple

import numpy as np
import pandas as pd

from data_to_paper.run_gpt_code.base_run_contexts import RunContext
from data_to_paper.run_gpt_code.run_issues import CodeProblem, RunIssue
from data_to_paper.utils.mutable import Flag
from data_to_paper.utils.operator_value import OperatorValue

P_VALUE_MIN = 1e-6  # values smaller than this will be formatted as "<1e-6"
EPSILON = 1e-12  # 0 is formatted as "1e-12"

# We show to the LLM 0 pvalues as some small epsilon sot that it will not attempt to fix them.
# These values will be formatted as "<1e-6" in the latex tables.


class OnStr(Enum):
    RAISE = 0
    AS_FLOAT = 1
    SMALLER_THAN = 2  # with P_VALUE_MIN, e.g. "<1e-6"
    LATEX_SMALLER_THAN = 3  # with P_VALUE_MIN, e.g. "$<1e-6$"
    WITH_EPSILON = 3  # with EPSILON, e.g. "1e-12"
    WITH_ZERO = 4  # just format. no minimal value
    DEBUG = 5


def format_p_value(x, minimal_value=P_VALUE_MIN, smaller_than_sign: str = '<'):
    """
    Format a p-value to a string.
    """
    if not isinstance(x, numbers.Number):
        return x
    if x > 1 or x < 0:
        raise ValueError(f"p-value should be in the range [0, 1]. Got: {x}")
    if np.isinf(x) or np.isnan(x):
        return str(x)
    if x >= minimal_value:
        return "{:.3g}".format(x)
    return smaller_than_sign + "{}".format(minimal_value)


@dataclass
class InvalidPValueRunIssue(RunIssue):
    """
    An issue that is raised when a p-value is invalid.
    """
    value_str: str = None
    func_call_str: str = None
    var_name: str = None
    issue: str = 'The function returned a p-value of {value_str}{for_var}.\n{call_str}'
    instructions: str = 'Please see if you understand why this is happening and fix it.'
    code_problem: CodeProblem = CodeProblem.RuntimeError

    @property
    def call_str(self):
        return f'\nThe function was called as: \n{self.func_call_str}\n\n' if self.func_call_str else ''

    @property
    def for_var(self):
        return f' for variable `{self.var_name}`' if self.var_name else ''


class PValue(OperatorValue):
    """
    An object that represents a p-value float.
    """

    # Sensible operators to perform on p-values:
    OPERATORS_RETURNING_NEW_PVALUE = {'__mul__', '__truediv__', '__floordiv__'}
    OPERATORS_RETURNING_NORMAL_VALUE = {'__eq__', '__ne__', '__lt__', '__le__', '__gt__', '__ge__',
                                        '__bool__', '__hash__'}
    # All other operators are not allowed

    BEHAVE_NORMALLY = Flag(False)
    ON_STR = OnStr.RAISE
    error_message_on_forbidden_func = "Calling `{func_name}` on a PValue object is forbidden.\n"
    this_is_a_p_value = True

    def __init__(self, value, created_by: str = None, var_name: str = None):
        super().__init__(value)
        self.created_by = created_by
        self.var_name = var_name

    def _get_new_object(self, value):
        return self.__class__(value, created_by=self.created_by, var_name=self.var_name)

    def _raise_if_forbidden_func(self, method_name):
        raise RunIssue.from_current_tb(
            category='Be careful with p-values',
            issue=self.error_message_on_forbidden_func.format(func_name=method_name, created_by=self.created_by),
            code_problem=CodeProblem.RuntimeError,
        )

    def _apply_post_operator(self, op, method_name, value):
        if self.BEHAVE_NORMALLY:
            return value
        if method_name in ['__str__', '__repr__']:
            on_str = self.ON_STR
            if on_str == OnStr.AS_FLOAT:
                return value
            if on_str == OnStr.SMALLER_THAN:
                return format_p_value(self.value, minimal_value=P_VALUE_MIN, smaller_than_sign='<')
            if on_str == OnStr.LATEX_SMALLER_THAN:
                return format_p_value(self.value, minimal_value=P_VALUE_MIN, smaller_than_sign='$<$')
            if on_str == OnStr.WITH_EPSILON:
                return format_p_value(self.value, minimal_value=EPSILON, smaller_than_sign='')
            if on_str == OnStr.WITH_ZERO:
                return format_p_value(self.value, minimal_value=0, smaller_than_sign='')
            if on_str == OnStr.DEBUG:
                return f'PValue({value})'
            if on_str == OnStr.RAISE:
                self._raise_if_forbidden_func(method_name)
            assert False, f'Unknown value for ON_STR: {on_str}'
        if method_name in self.OPERATORS_RETURNING_NEW_PVALUE:
            return self._get_new_object(value)
        if method_name in self.OPERATORS_RETURNING_NORMAL_VALUE:
            return value
        self._raise_if_forbidden_func(method_name)

    @property
    def __class__(self):
        if self.BEHAVE_NORMALLY or self.ON_STR != OnStr.RAISE and self.ON_STR != OnStr.AS_FLOAT:
            return PValue
        return type(self.value)

    @classmethod
    def from_value(cls, value, created_by: str = None, var_name: str = None,
                   raise_on_nan: bool = True, raise_on_one: bool = True,
                   func_call_str: str = None, context: RunContext = None):

        if raise_on_nan and np.isnan(value):
            value_str = 'NaN'
        elif raise_on_one and value == 1:
            value_str = '1'
        else:
            value_str = None

        if value_str is not None:
            run_issue = InvalidPValueRunIssue.from_current_tb(
                category='Wrong p-value',
                value_str=value_str,
                func_call_str=func_call_str,
                var_name=var_name,
            )
            if context is None:
                raise run_issue
            context.issues.append(run_issue)

        return cls(value, created_by=created_by, var_name=var_name)

    @classmethod
    def reconstruction(cls, value, created_by: str = None, var_name: str = None):
        return cls(value, created_by=created_by, var_name=var_name)

    def __reduce__(self):
        return self.reconstruction, (self.value, self.created_by, self.var_name)


def convert_to_p_value(value, created_by: str = None, var_name: str = None,
                       raise_on_nan: bool = True, raise_on_one: bool = True,
                       func_call_str: str = None, context: RunContext = None):
    if is_p_value(value):
        return value
    kwargs = dict(created_by=created_by, var_name=var_name,
                  raise_on_nan=raise_on_nan, raise_on_one=raise_on_one,
                  func_call_str=func_call_str, context=context)
    if isinstance(value, float):
        return PValue.from_value(value, **kwargs)
    if isinstance(value, np.ndarray):
        return np.vectorize(convert_to_p_value)(value, **kwargs)
    if isinstance(value, pd.Series):
        kwargs.pop('var_name')
        for i in range(len(value)):
            value.iloc[i] = convert_to_p_value(value.iloc[i], var_name=value.index[i], **kwargs)
        return value
    if isinstance(value, list):
        return [convert_to_p_value(val, **kwargs) for val in value]
    if isinstance(value, dict):
        return {key: convert_to_p_value(val, **kwargs) for key, val in value.items()}


def is_p_value(value):
    return hasattr(value, 'this_is_a_p_value')


def is_containing_p_value(value):
    if is_p_value(value):
        return True
    if isinstance(value, np.ndarray):
        return np.any(np.vectorize(is_containing_p_value)(value))
    if isinstance(value, pd.Series):
        return value.apply(is_containing_p_value).any()
    if isinstance(value, pd.DataFrame):
        return value.applymap(is_containing_p_value).any().any()
    if isinstance(value, (list, tuple)):
        return any(is_containing_p_value(val) for val in value)
    if isinstance(value, dict):
        return any(is_containing_p_value(val) for val in value.values())
    return False


@dataclass
class TrackPValueCreationFuncs(RunContext):
    package_names: Iterable[str] = ()
    pvalue_creating_funcs: List[str] = field(default_factory=list)

    def _add_pvalue_creating_func(self, func_name: str):
        if self._is_enabled and self._is_called_from_user_script(4):
            self.pvalue_creating_funcs.append(func_name)


class OnStrPValue:
    """
    A context manager for temporarily changing the ON_STR value of PValue.
    """
    def __init__(self, on_str: Optional[OnStr] = None):
        self.on_str = on_str
        self.prev_on_str = PValue.ON_STR

    def __enter__(self):
        if self.on_str is not None:
            PValue.ON_STR = self.on_str

    def __exit__(self, exc_type, exc_val, exc_tb):
        PValue.ON_STR = self.prev_on_str
        return False


class PValueToStars:
    default_levels = (0.01, 0.001, 0.0001)

    def __init__(self, p_value: Optional[float] = None, levels: Tuple[float] = None):
        self.p_value = p_value
        self.levels = levels or self.default_levels

    def __str__(self):
        return self.convert_to_stars()

    def convert_to_stars(self):
        p_value = self.p_value
        levels = self.levels
        if p_value < levels[2]:
            return '***'
        if p_value < levels[1]:
            return '**'
        if p_value < levels[0]:
            return '*'
        return 'NS'

    def get_conversion_legend_text(self) -> str:
        #  NS p >= 0.01, * p < 0.01, ** p < 0.001, *** p < 0.0001
        levels = self.levels
        legend = [f'NS p >= {levels[0]}']
        for i, level in enumerate(levels):
            legend.append(f'{(i + 1) * "*"} p < {level}')
        return ', '.join(legend)
