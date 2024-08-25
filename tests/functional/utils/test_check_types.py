import pytest

from typing import List, Dict, Optional
from data_to_paper.utils.check_type import validate_value_type, WrongTypeException, raise_on_wrong_func_argument_types


@pytest.mark.parametrize('value, type_, expected', [
    (3, int, None),
    ([1, 2, 3], list, None),
    ([1, 2, 3], List, None),
    ([], List, None),
    (['abc', 1], List[str], "object within the list must be of type `str`"),
    (['abc', ''], List[str], None),
    ([], Dict[str, int], "object must be of type `dict`"),
    ({'a': 1}, Dict[str, int], None),
    ({'a': 1, 'b': 2.2}, Dict[str, int], "object within the dict values must be of type `int`"),
    ({'x': ['aaa', 'bbb']}, Dict[str, List[str]], None),
    ({'x': ['aaa', 2]}, Dict[str, List[str]], "object within the list within the dict values must be of type `str`"),
])
def test_validate_value_type(value, type_, expected):
    if expected is None:
        validate_value_type(value, type_)
    else:
        with pytest.raises(WrongTypeException) as e:
            validate_value_type(value, type_)
        assert e.value.message == expected


@pytest.mark.parametrize('s, d, l, o, msg', [
    ('abc', {'a': 1}, ['a', 'b'], None, None),
    ('abc', {'a': 1}, ['a', 'b'], 'ok', None),
    ('abc', {'a': 1}, ['a', 1], 'ok', "list"),
    ('abc', {'a': 'c'}, ['a', 'b'], 'ok', "dict values"),
    (73, {'a': 1}, ['a', 'b'], 'ok', "str"),
    ('abc', {'a': 1}, ['a', 'b'], 3, "str, NoneType"),
])
def test_raise_on_wrong_variable_types(s, d, l, o, msg):
    def func(s: str, d: Dict[str, int], l: List[str], o: Optional[str]):
        pass
    if msg is None:
        raise_on_wrong_func_argument_types(func, s, d, l=l, o=o)
    else:
        with pytest.raises(WrongTypeException) as e:
            raise_on_wrong_func_argument_types(func, s, d, l=l, o=o)
        assert msg in e.value.message
