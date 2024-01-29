from data_to_paper.utils.operator_value import OperatorValue


class TestOperatorValue(OperatorValue):
    OPERATORS_RETURNING_NEW_OBJECT = {'__add__', '__radd__', '__sub__', '__rsub__', '__neg__', '__pos__'}


def test_binary_operator_value():
    a = TestOperatorValue(1)
    assert a == 1
    assert isinstance(a + 2, TestOperatorValue)
    assert isinstance(2 + a, TestOperatorValue)
    assert isinstance(a + a, TestOperatorValue)
    assert isinstance(a * 2, int)
    assert isinstance(2 * a, int)
    assert a + 2 == 3
    assert - a < 0
    assert a + a == 2


def test_binary_operator_value_with_additional_args():
    a = TestOperatorValue(1.2345)
    assert round(a, 2) == 1.23
