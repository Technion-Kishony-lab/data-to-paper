import functools
from dataclasses import dataclass, field
from typing import List, Iterable

import numpy as np
import pandas as pd

from data_to_paper.run_gpt_code.base_run_contexts import RunContext
from data_to_paper.run_gpt_code.run_issues import CodeProblem, RunIssue
from data_to_paper.utils.mutable import Flag
from data_to_paper.utils.operator_value import OperatorValue


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
    allow_str = Flag(False)
    error_message_on_forbidden_func = "Calling `{func_name}` on a PValue object is forbidden.\n"
    this_is_a_p_value = True

    def __init__(self, value, created_by: str = None, var_name: str = None):
        super().__init__(value)
        self.created_by = created_by
        self.var_name = var_name

    def _forbidden_func(self, func):
        if self.allow_str:
            return func(self.value)
        raise RunIssue.from_current_tb(
            issue=self.error_message_on_forbidden_func.format(func_name=func.__name__,
                                                              created_by=self.created_by),
            code_problem=CodeProblem.RuntimeError,
        )

    @property
    def __class__(self):
        if not self.allow_str:
            return type(self.value)
        return PValue

    def __str__(self):
        return self._forbidden_func('{:.4g}'.format)

    def __repr__(self):
        return self._forbidden_func('{:.4g}'.format)

    def __float__(self):
        return self._forbidden_func(float)

    @classmethod
    def from_value(cls, value, created_by: str = None, var_name: str = None,
                   raise_on_nan: bool = True,  raise_on_one: bool = True,
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
