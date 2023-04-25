import pytest

from scientistgpt.utils.text_utils import NiceList


@pytest.mark.parametrize('nice_list, expected_repr', [
    (NiceList(), ''),
    (NiceList(['a']), 'a'),
    (NiceList(['a', 'b']), 'a and b'),
    (NiceList(['a', 'b', 'c']), 'a, b and c'),
    (NiceList(['a', 'b', 'c'], wrap_with='`'), '`a`, `b` and `c`'),
    (NiceList(['a', 'b', 'c'], prefix='{} file[s]: '), '3 files: a, b and c'),

])
def test_nice_list(nice_list, expected_repr):
    assert repr(nice_list) == expected_repr