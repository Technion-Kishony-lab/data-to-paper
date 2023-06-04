import pytest

from scientistgpt.utils.check_numeric_values import extract_numeric_values, find_non_matching_numeric_values


@pytest.mark.parametrize('text, numbers', [
    ('The p-value was 1.02 and the variance was 10.00', ['1.02', '10.00']),
    ('The number of patients was 200,000', ['200,000']),
    ('There were three numbers 10, 3 and 9', ['10', '3', '9']),
    ('Some results can be negative, like -100.2', ['-100.2']),
])
def test_extract_numeric_values(text, numbers):
    assert extract_numeric_values(text) == numbers


@pytest.mark.parametrize('source, non_matching', [
    ('p-value 1.0187912, variance 10.0000001', []),
    ('p-value 1.0272333, variance 10.0000001', ['1.02']),
    ('p-value 1.0272333, variance 10.01', ['1.02', '10.00']),
])
def test_find_non_matching_numeric_values(source, non_matching):
    target = 'p-value 1.02, variance 10.00'
    assert find_non_matching_numeric_values(source, target) == non_matching


@pytest.mark.parametrize('source, non_matching', [
    ('rows: 234091, cols: 9', []),
])
def test_find_non_matching_numeric_values_for_numbers_with_comma(source, non_matching):
    target = 'We had 234,091 rows and 9 columns'
    assert find_non_matching_numeric_values(source, target) == non_matching


@pytest.mark.parametrize('source, non_matching', [
    ('accuracy of 0.900154, FDR 0.0021, AUC of 0.7524921', []),
    ('accuracy of 0.9002, FDR 0.0021, AUC of 0.7525', []),
])
def test_find_non_matching_numeric_values_with_percentage(source, non_matching):
    target = 'accuracy of 90.02%, AUC of 75.25% and FDR 0.2%'
    assert find_non_matching_numeric_values(source, target) == non_matching
