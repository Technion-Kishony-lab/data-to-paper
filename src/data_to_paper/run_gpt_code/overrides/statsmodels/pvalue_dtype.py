# pragma: no cover
"""
This file is obsolete. It was used to create a custom p-value dtype for statsmodels to be used with
PValueFloat which inherits from float.
We now use a PValue object class instead of the PValueFloat(float) class.
"""


from __future__ import annotations

import operator
import re
from typing import Any, Sequence

import numpy as np
import pandas as pd
from pandas.core.dtypes.dtypes import PandasExtensionDtype
from pandas.core.indexers import check_array_indexer


class PValueFloat(float):
    pass


# Based on:
# https://stackoverflow.com/questions/68893521/simple-example-of-pandas-extensionarray:

@pd.api.extensions.register_extension_dtype
class PValueDtype(PandasExtensionDtype):
    """
    An ExtensionDtype for func-aware angular data.
    """
    # Required for all parameterized dtypes
    _metadata = ('func',)
    _match = re.compile(pattern=r'(P|p)value\[(?P<func>.+)\]')
    name = 'pvalue'

    def __init__(self, func=None):
        self._func = func

    def __str__(self) -> str:
        return f'pvalue[{self.func}]'

    # TestDtypeTests
    def __hash__(self) -> int:
        return hash(str(self))

    # TestDtypeTests
    def __eq__(self, other: Any) -> bool:
        if isinstance(other, str):
            return self.name == other
        else:
            return isinstance(other, type(self)) and self.func == other.func

    # Required for pickle compat (see GH26067)
    def __setstate__(self, state) -> None:
        self._func = state['func']

    # Required for all ExtensionDtype subclasses
    @classmethod
    def construct_array_type(cls):
        """
        Return the array type associated with this dtype.
        """
        return PValueArray

    # Required for all ExtensionDtype subclasses
    @property
    def type(self):
        """
        The scalar type for the array (e.g., int).
        """
        return np.float64

    @property
    def func(self) -> str:
        """
        The function used to compute the p-value.
        """
        return self._func


class PValueArray(pd.api.extensions.ExtensionArray):
    """
    An ExtensionArray for func-aware p-values.
    """

    # Include `copy` param for TestInterfaceTests
    def __init__(self, data, func=None, copy: bool = False):
        self._data = np.array(data, copy=copy)
        self._func = func

    # Required for all ExtensionArray subclasses
    def __getitem__(self, index: int) -> PValueArray | Any:
        """
        Select a subset of self.
        """
        if isinstance(index, int):
            return PValueFloat(self._data[index])
        else:
            # Check index for TestGetitemTests
            index = check_array_indexer(self, index)
            return type(self)(self._data[index])

    # TestSetitemTests
    def __setitem__(self, index: int, value: np.generic) -> None:
        """
        Set one or more values in-place.
        """
        # Check index for TestSetitemTests
        index = check_array_indexer(self, index)

        # Upcast to value's type (if needed) for TestMethodsTests
        if self._data.dtype < type(value):
            self._data = self._data.astype(type(value))

        # TODO: Validate value for TestSetitemTests
        # value = self._validate_setitem_value(value)

        self._data[index] = value

    # Required for all ExtensionArray subclasses
    def __len__(self) -> int:
        """
        Length of this array.
        """
        return len(self._data)

    # TestUnaryOpsTests
    def __invert__(self) -> PValueArray:
        """
        Element-wise inverse of this array.
        """
        data = ~self._data
        return type(self)(data, func=self.dtype.func)

    def _apply_operator(self, op, other, recast=False) -> np.ndarray | PValueArray:
        """
        Helper method to apply an operator `op` between `self` and `other`.

        Some ops require the result to be recast into PValueArray:
        * Comparison ops: recast=False
        * Arithmetic ops: recast=True
        """
        f = operator.attrgetter(op)
        data, other = np.array(self), np.array(other)
        result = f(data)(other)
        return result if not recast else type(self)(result, func=self.dtype.func)

    def _apply_operator_if_not_series(self, op, other, recast=False) -> np.ndarray | PValueArray:
        """
        Wraps _apply_operator only if `other` is not Series/DataFrame.

        Some ops should return NotImplemented if `other` is a Series/DataFrame:
        https://github.com/pandas-dev/pandas/blob/e7e7b40722e421ef7e519c645d851452c70a7b7c/pandas/tests/extension/base/ops.py#L115
        """
        if isinstance(other, (pd.Series, pd.DataFrame)):
            return NotImplemented
        else:
            return self._apply_operator(op, other, recast=recast)

    # Required for all ExtensionArray subclasses
    @pd.core.ops.unpack_zerodim_and_defer('__eq__')
    def __eq__(self, other):
        return self._apply_operator('__eq__', other, recast=False)

    # TestComparisonOpsTests
    @pd.core.ops.unpack_zerodim_and_defer('__ne__')
    def __ne__(self, other):
        return self._apply_operator('__ne__', other, recast=False)

    # TestComparisonOpsTests
    @pd.core.ops.unpack_zerodim_and_defer('__lt__')
    def __lt__(self, other):
        return self._apply_operator('__lt__', other, recast=False)

    # TestComparisonOpsTests
    @pd.core.ops.unpack_zerodim_and_defer('__gt__')
    def __gt__(self, other):
        return self._apply_operator('__gt__', other, recast=False)

    # TestComparisonOpsTests
    @pd.core.ops.unpack_zerodim_and_defer('__le__')
    def __le__(self, other):
        return self._apply_operator('__le__', other, recast=False)

    # TestComparisonOpsTests
    @pd.core.ops.unpack_zerodim_and_defer('__ge__')
    def __ge__(self, other):
        return self._apply_operator('__ge__', other, recast=False)

    # TestArithmeticOpsTests
    @pd.core.ops.unpack_zerodim_and_defer('__add__')
    def __add__(self, other) -> PValueArray:
        return self._apply_operator_if_not_series('__add__', other, recast=True)

    # TestArithmeticOpsTests
    @pd.core.ops.unpack_zerodim_and_defer('__sub__')
    def __sub__(self, other) -> PValueArray:
        return self._apply_operator_if_not_series('__sub__', other, recast=True)

    # TestArithmeticOpsTests
    @pd.core.ops.unpack_zerodim_and_defer('__mul__')
    def __mul__(self, other) -> PValueArray:
        return self._apply_operator_if_not_series('__mul__', other, recast=True)

    # TestArithmeticOpsTests
    @pd.core.ops.unpack_zerodim_and_defer('__truediv__')
    def __truediv__(self, other) -> PValueArray:
        return self._apply_operator_if_not_series('__truediv__', other, recast=True)

    # Required for all ExtensionArray subclasses
    @classmethod
    def _from_sequence(cls, data, dtype=None, copy: bool = False):
        """
        Construct a new PValueArray from a sequence of scalars.
        """
        if dtype is None:
            dtype = PValueDtype()

        if not isinstance(dtype, PValueDtype):
            msg = f"'{cls.__name__}' only supports 'PValueDtype' dtype"
            raise ValueError(msg)
        else:
            return cls(data, func=dtype.func, copy=copy)

    # TestParsingTests
    @classmethod
    def _from_sequence_of_strings(cls, strings, *, dtype=None, copy: bool = False) -> PValueArray:
        """
        Construct a new PValueArray from a sequence of strings.
        """
        scalars = pd.to_numeric(strings, errors='raise')
        return cls._from_sequence(scalars, dtype=dtype, copy=copy)

    # Required for all ExtensionArray subclasses
    @classmethod
    def _from_factorized(cls, uniques: np.ndarray, original: PValueArray):
        """
        Reconstruct an PValueArray after factorization.
        """
        return cls(uniques, func=original.dtype.func)

    # Required for all ExtensionArray subclasses
    @classmethod
    def _concat_same_type(cls, to_concat: Sequence[PValueArray]) -> PValueArray:
        """
        Concatenate multiple AngleArrays.
        """
        return cls(np.concatenate(to_concat), func=None)

    # Required for all ExtensionArray subclasses
    @property
    def dtype(self):
        """
        An instance of PValueDtype.
        """
        return PValueDtype(self._func)

    # Required for all ExtensionArray subclasses
    @property
    def nbytes(self) -> int:
        """
        The number of bytes needed to store this object in memory.
        """
        return self._data.nbytes

    @property
    def func(self):
        return self.dtype.func

    # Test*ReduceTests
    def all(self) -> bool:
        return all(self)

    def any(self) -> bool:  # Test*ReduceTests
        return any(self)

    def sum(self) -> np.generic:  # Test*ReduceTests
        return self._data.sum()

    def mean(self) -> np.generic:  # Test*ReduceTests
        return self._data.mean()

    def max(self) -> np.generic:  # Test*ReduceTests
        return self._data.max()

    def min(self) -> np.generic:  # Test*ReduceTests
        return self._data.min()

    def prod(self) -> np.generic:  # Test*ReduceTests
        return self._data.prod()

    def std(self) -> np.generic:  # Test*ReduceTests
        return pd.Series(self._data).std()

    def var(self) -> np.generic:  # Test*ReduceTests
        return pd.Series(self._data).var()

    def median(self) -> np.generic:  # Test*ReduceTests
        return np.median(self._data)

    def skew(self) -> np.generic:  # Test*ReduceTests
        return pd.Series(self._data).skew()

    def kurt(self) -> np.generic:  # Test*ReduceTests
        return pd.Series(self._data).kurt()

    # Test*ReduceTests
    def _reduce(self, name: str, *, skipna: bool = True, **kwargs):
        """
        Return a scalar result of performing the reduction operation.
        """
        f = operator.attrgetter(name)
        return f(self)()

    # Required for all ExtensionArray subclasses
    def isna(self):
        """
        A 1-D array indicating if each value is missing.
        """
        return pd.isnull(self._data)

    # Required for all ExtensionArray subclasses
    def copy(self):
        """
        Return a copy of the array.
        """
        copied = self._data.copy()
        return type(self)(copied, func=self.func)

    # Required for all ExtensionArray subclasses
    def take(self, indices, allow_fill=False, fill_value=None):
        """
        Take elements from an array.
        """
        if allow_fill and fill_value is None:
            fill_value = self.dtype.na_value

        result = pd.core.algorithms.take(self._data, indices, allow_fill=allow_fill,
                                         fill_value=fill_value)
        return self._from_sequence(result)

    # TestMethodsTests
    def value_counts(self, dropna: bool = True):
        """
        Return a Series containing descending counts of unique values (excludes NA values by default).
        """
        return pd.core.algorithms.value_counts(self._data, dropna=dropna)
