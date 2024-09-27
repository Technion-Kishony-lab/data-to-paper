import pytest

from data_to_paper.run_gpt_code.code_utils import add_label_to_first_triple_quotes_if_missing
from data_to_paper.text.text_numeric_formatting import round_floats


@pytest.mark.parametrize('text, expected', [
    ('1.2345678901234567', '1.235'),
    ('1.2345678901234567e-09', '1.235e-09'),
    ('1.2345678901234567e+09', '1.235e+09'),
    ('1.234567', '1.234567'),
    ('1.23456789e-9', '1.23456789e-9'),
    ('12345678901234567', '12345678901234567'),
    ('Sobel test statistic: 37.793751174052424, p-value: 0.0', 'Sobel test statistic: 37.79, p-value: 0.0'),
])
def test_replace_floats(text, expected):
    assert round_floats(text, pad_with_spaces=False) == expected


@pytest.mark.parametrize('text, expected', [
    ('my code: ```python\nprint("hello")\n```', 'my code: ```python\nprint("hello")\n```'),
    ('my code: ```\nprint("hello")\n```', 'my code: ```python\nprint("hello")\n```'),
])
def test_add_label_to_first_triple_quotes_if_missing(text, expected):
    assert add_label_to_first_triple_quotes_if_missing(text, 'python') == expected
