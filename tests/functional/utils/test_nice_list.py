import pytest

from scientistgpt.utils.nice_list import NiceList


@pytest.mark.parametrize('nice_list, expected_repr', [
    (NiceList(), ''),
    (NiceList(['a']), 'a'),
    (NiceList(['a', 'b']), 'a, b'),
    (NiceList(['a', 'b', 'c'], last_separator=' and '), 'a, b and c'),
    (NiceList(['a', 'b', 'c'], wrap_with='`', last_separator=' and '), '`a`, `b` and `c`'),
    (NiceList(['a', 'b', 'c'], prefix='{} file[s]: ', last_separator=' and '), '3 files: a, b and c'),

])
def test_nice_list(nice_list, expected_repr):
    assert repr(nice_list) == expected_repr
