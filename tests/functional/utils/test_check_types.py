import pytest

from typing import List, Dict, Optional, Union, Tuple
from data_to_paper.utils.check_type import validate_value_type, WrongTypeException, raise_on_wrong_func_argument_types


@pytest.mark.parametrize('value, type_, expected', [
    (3, int, None),
    ([1, 2, 3], list, None),
    ([1, 2, 3], List, None),
    ([], List, None),
    (['abc', 1], List[str], "object within the list must be of type `str` (but found `int`)"),
    (['abc', ''], List[str], None),
    ([], Dict[str, int], "object must be of type `dict` (but found `list`)"),
    ({'a': 1}, Dict[str, int], None),
    ({'a': 1, 'b': 2.2}, Dict[str, int], "object within the dict values must be of type `int` (but found `float`)"),
    ({'x': ['aaa', 'bbb']}, Dict[str, List[str]], None),
    ({'x': ['aaa', 2]}, Dict[str, List[str]], "object within the list within the dict values must be of type `str` "
                                              "(but found `int`)"),
    (0, Union[int, str], None),
    (None, Union[int, str, None], None),
    (None, Union[int, str, type(None)], None),
    ((1, 2), Tuple[int], "object must be a tuple of length 1 (but found a tuple of length 2)"),
    ((1, 2), Tuple[int, ...], None),
    ((1, "2"), Tuple[int, str], None),
    ((1, 2), Tuple[int, str], "object within the tuple must be of type `str` (but found `int`)"),
    (None, Union[int, str], 'object must be of one of the types: int, str (but found `NoneType`)'),
    (0.7, Union[int, List[int]], "object must be of one of the types: int, List[int] (but found `float`)"),
    (0.7, Union[int, str], "object must be of one of the types: int, str (but found `float`)"),
])
def test_validate_value_type(value, type_, expected):
    if expected is None:
        validate_value_type(value, type_)
    else:
        with pytest.raises(WrongTypeException) as e:
            validate_value_type(value, type_)
        assert str(e.value) == expected


@pytest.mark.parametrize("s_, d_, l_, o_, msg", [
    ('abc', {'a': 1}, ['a', 'b'], None, None),
    ('abc', {'a': 1}, ['a', 'b'], 'ok', None),
    ('abc', {'a': 1}, ['a', 1], 'ok', "list"),
    ('abc', {'a': 'c'}, ['a', 'b'], 'ok', "dict values"),
    (73, {'a': 1}, ['a', 'b'], 'ok', "str"),
    ('abc', {'a': 1}, ['a', 'b'], 3, "str, NoneType"),
])
def test_raise_on_wrong_variable_types(s_, d_, l_, o_, msg):
    def func(s: str, d: Dict[str, int], l: List[str], o: Optional[str]):  # noqa
        pass
    if msg is None:
        raise_on_wrong_func_argument_types(func, s_, d_, l=l_, o=o_)
    else:
        with pytest.raises(TypeError) as e:
            raise_on_wrong_func_argument_types(func, s_, d_, l=l_, o=o_)
        assert msg in str(e.value)
