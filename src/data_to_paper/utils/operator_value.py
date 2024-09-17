import operator

import numpy as np


class OperatorValue:
    OPERATORS_RETURNING_NEW_OBJECT = {}

    UNARY_METHODS_TO_OPERATORS = {
        '__neg__': operator.neg,
        '__pos__': operator.pos,
        '__abs__': operator.abs,
        '__invert__': operator.invert,
        '__round__': round,
        '__float__': float,
        '__floor__': np.floor,
        '__ceil__': np.ceil,
        '__trunc__': np.trunc,
        '__hash__': hash,
        '__format__': format,
        '__str__': str,
        '__repr__': repr,
        '__bool__': bool,
    }

    BINARY_METHODS_TO_OPERATORS = {
        '__lt__': operator.lt,
        '__le__': operator.le,
        '__eq__': operator.eq,
        '__ne__': operator.ne,
        '__gt__': operator.gt,
        '__ge__': operator.ge,
        '__add__': operator.add,
        '__sub__': operator.sub,
        '__mul__': operator.mul,
        '__truediv__': operator.truediv,
        '__floordiv__': operator.floordiv,
        '__mod__': operator.mod,
        '__pow__': operator.pow,
        '__lshift__': operator.lshift,
        '__rshift__': operator.rshift,
        '__and__': operator.and_,
        '__xor__': operator.xor,
        '__or__': operator.or_,
        '__radd__': operator.add,
        '__rsub__': operator.sub,
        '__rmul__': operator.mul,
        '__rtruediv__': operator.truediv,
        '__rfloordiv__': operator.floordiv,
        '__rmod__': operator.mod,
        '__rpow__': operator.pow,
        '__rlshift__': operator.lshift,
        '__rrshift__': operator.rshift,
        '__rand__': operator.and_,
        '__rxor__': operator.xor,
        '__ror__': operator.or_,
    }

    def __init__(self, value):
        self.value = value

    def _get_new_object(self, value):
        return self.__class__(value)

    def _apply_post_operator(self, op, method_name, value):
        if method_name in self.OPERATORS_RETURNING_NEW_OBJECT:
            return self._get_new_object(value)
        return value

    def _raise_on_forbidden_operator(self, op, method_name):
        if op is None:
            raise NotImplementedError(f'Operator {method_name} is not allowed on {self.__class__.__name__}')

    def _binary_op(self, other, op, method_name):
        self._raise_on_forbidden_operator(op, method_name)
        if isinstance(other, OperatorValue):
            other = other.value
        return self._apply_post_operator(op, method_name, op(self.value, other))

    def _unary_op(self, op, *args, method_name=None, **kwargs):
        self._raise_on_forbidden_operator(op, method_name)
        return self._apply_post_operator(op, method_name, op(self.value, *args, **kwargs))

    @classmethod
    def add_methods(cls):
        for method_name, op in cls.BINARY_METHODS_TO_OPERATORS.items():
            def method(self, other, op=op, method_name=method_name):
                return self._binary_op(other, op, method_name)
            setattr(cls, method_name, method)

        for method_name, op in cls.UNARY_METHODS_TO_OPERATORS.items():
            def method(self, *args, op=op, method_name=method_name, **kwargs):
                return self._unary_op(op, *args, method_name=method_name, **kwargs)
            setattr(cls, method_name, method)
        return cls


OperatorValue.add_methods()
