import functools

import numpy as np
import pandas as pd

from data_to_paper.run_gpt_code.types import RunUtilsError, RunIssue, CodeProblem
from data_to_paper.utils.mutable import Flag, Mutable
from data_to_paper.utils.operator_value import OperatorValue


class PValue(OperatorValue):
    """
    An object that represents a p-value float.
    """
    allow_str = Flag(False)
    error_message_on_forbidden_func = Mutable("Calling `{func_name}` on a PValue object is forbidden.\n")
    this_is_a_p_value = True

    def __init__(self, value, created_by: str = None):
        super().__init__(value)
        self.created_by = created_by

    def _forbidden_func(self, func):
        if self.allow_str:
            return func(self.value)
        raise RunUtilsError(
            RunIssue(
                issue=self.error_message_on_forbidden_func.val.format(func_name=func.__name__,
                                                                      created_by=self.created_by),
                code_problem=CodeProblem.RuntimeError,
            )
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
    def from_value(cls, value, created_by: str = None, raise_on_nan: bool = True, func_call_str: str = None):
        if isinstance(value, cls):
            return value
        if raise_on_nan and np.isnan(value):
            call_str = f'\nThe function was called as: \n{func_call_str}\n\n' if func_call_str else ''
            raise RunUtilsError(
                RunIssue(
                    issue=f'The function returned a p-value of NaN.\n{call_str}',
                    code_problem=CodeProblem.RuntimeError,
                    instructions='Please see if you understand why this is happening and fix it.',
                )
            )
        return cls(value, created_by=created_by)


def convert_to_p_value(value, created_by: str = None, raise_on_nan: bool = True, func_call_str: str = None):
    if is_p_value(value):
        return value
    kwargs = dict(created_by=created_by, raise_on_nan=raise_on_nan, func_call_str=func_call_str)
    if isinstance(value, float):
        return PValue.from_value(value, **kwargs)
    if isinstance(value, np.ndarray):
        return np.vectorize(PValue.from_value)(value, **kwargs)
    if isinstance(value, pd.Series):
        return value.apply(functools.partial(PValue.from_value, **kwargs))
    if isinstance(value, list):
        return [convert_to_p_value(val, **kwargs) for val in value]
    if isinstance(value, dict):
        return {key: convert_to_p_value(val, **kwargs) for key, val in value.items()}


def is_p_value(value):
    return hasattr(value, 'this_is_a_p_value')
