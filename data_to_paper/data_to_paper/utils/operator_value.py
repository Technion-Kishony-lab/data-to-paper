import operator

import numpy as np


class OperatorValue:
    UNARY_METHODS_TO_OPERATORS = {
        '__neg__': operator.neg,
        '__pos__': operator.pos,
        '__abs__': operator.abs,
        '__invert__': operator.invert,
        '__round__': round,
        '__floor__': np.floor,
        '__ceil__': np.ceil,
        '__trunc__': np.trunc,
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

    def __eq__(self, other):
        return self.value == other.value

    def __hash__(self):
        return hash(self.value)

    def __float__(self):
        return self.value

    def __format__(self, format_spec):
        return format(self.value, format_spec)

    def __str__(self):
        return str(self.value)

    def _binary_op(self, other, op):
        if isinstance(other, OperatorValue):
            other = other.value
        return op(self.value, other)

    @classmethod
    def add_methods(cls):
        for method_name, op in cls.BINARY_METHODS_TO_OPERATORS.items():
            def method(self, other, op=op):
                if op is None:
                    raise NotImplementedError(f'Operator {method_name} is not allowed on {self.__class__.__name__}')
                return self._binary_op(other, op)
            setattr(cls, method_name, method)

        for method_name, op in cls.UNARY_METHODS_TO_OPERATORS.items():
            def method(self, op=op):
                if op is None:
                    raise NotImplementedError(f'Operator {method_name} is not allowed on {self.__class__.__name__}')
                return op(self.value)
            setattr(cls, method_name, method)
        return cls


OperatorValue.add_methods()
