import pytest

from data_to_paper.run_gpt_code.overrides.utils import round_floats


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
    assert round_floats(text) == expected
