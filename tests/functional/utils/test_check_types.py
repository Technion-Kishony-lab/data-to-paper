import pytest

from typing import List, Dict, Set
from scientistgpt.utils.check_type import validate_value_type, WrongTypeException


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
