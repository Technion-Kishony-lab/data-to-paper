from data_to_paper.utils.operator_value import OperatorValue


class TestBinaryOperatorValue(OperatorValue):
    pass


def test_binary_operator_value():
    a = TestBinaryOperatorValue(1)
    assert a == 1
    assert a + 2 == 3
    assert - a < 0
    assert a + a == 2


def test_binary_operator_value_with_additional_args():
    a = TestBinaryOperatorValue(1.2345)
    assert round(a, 2) == 1.23
