import functools

import numpy as np
import pandas as pd

from data_to_paper.utils.operator_value import OperatorValue


class PValue(OperatorValue):
    """
    An object that represents a p-value float.
    """

    def __init__(self, value, created_by: str = None):
        super().__init__(value)
        self.created_by = created_by

    def __str__(self):
        return f'PValue({self.value})'

    def __repr__(self):
        return str(self)

    @classmethod
    def from_value(cls, value, created_by: str = None):
        if isinstance(value, cls):
            return value
        return cls(value, created_by=created_by)


def convert_to_p_value(value, created_by: str = None):
    if isinstance(value, PValue):
        return value
    if isinstance(value, float):
        return PValue(value, created_by=created_by)
    if isinstance(value, np.ndarray):
        return np.vectorize(PValue.from_value)(value, created_by=created_by)
    if isinstance(value, pd.Series):
        return value.apply(functools.partial(PValue.from_value, created_by=created_by))
    if isinstance(value, list):
        return [convert_to_p_value(val, created_by=created_by) for val in value]
    if isinstance(value, dict):
        return {key: convert_to_p_value(val, created_by=created_by) for key, val in value.items()}

