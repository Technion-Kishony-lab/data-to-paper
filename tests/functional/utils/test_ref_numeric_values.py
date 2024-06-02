import pytest

from data_to_paper.code_and_output_files.file_view_params import ViewParams, ViewPurpose
from data_to_paper.code_and_output_files.ref_numeric_values import \
    ReferencedValue, find_hyperlinks, find_numeric_values, HypertargetFormat, HypertargetPosition
from data_to_paper.code_and_output_files.referencable_text import NumericReferenceableText, \
    LabeledNumericReferenceableText


@pytest.mark.parametrize('text, expected_text', [
    ('The number 1.2 is a numeric value.', r'The number \hypertarget{A0a}{1.2} is a numeric value.'),
    ('Numbers: 1.2e-3 and -7.8.', r'Numbers: \hypertarget{A0a}{1.2e-3} and \hypertarget{A0b}{-7.8}.'),
    ('In year 2015.', r'In year \hypertarget{A0a}{2015}.'),
])
def test_create_references_to_numeric_values(text, expected_text):
    assert NumericReferenceableText(text=text, hypertarget_prefix='A').get_formatted_text_and_references(
        ViewParams(hypertarget_format=HypertargetFormat(position=HypertargetPosition.WRAP)))[0] == expected_text


def test_labeled_numeric_referenceable_text():
    text = "Label @@<1.23>@@ and not this 7.89 value."
    numeric_ref = LabeledNumericReferenceableText(
        text=text,
        hypertarget_prefix='N',
        filename='numeric_values',
    )
    assert numeric_ref.get_hypertarget_text_with_header(
        ViewPurpose.HYPERTARGET_PRODUCT) == r"Label \hypertarget{N0a}{1.23} and not this 7.89 value."
    assert numeric_ref.get_hypertarget_text_with_header(
        ViewPurpose.PRODUCT) == r"Label 1.23 and not this 7.89 value."


@pytest.mark.parametrize('text, expected', [
    ('a 1,100 b', ['1,100']),
    ('a 1,100. b', ['1,100']),
    ('a 1,100.0 b', ['1,100.0']),
    ('a 12.3e-3 b', ['12.3e-3']),
    ('a +12.3e-3 -12.3e-3 b', ['+12.3e-3', '-12.3e-3']),
    ('a 12.3e-3,3 b', ['12.3e-3', '3']),
    ('a12.3 b', []),
    ('12.3 b', ['12.3']),
    ('#34 12.3e-3b', ['12.3e-3']),
    ('P <1e-3 wow!', ['1e-3']),
    ('P $<$1e-3 wow!', ['1e-3']),
    ('P=1e-3 wow!', ['1e-3']),
    (' 10,23,54', ['10', '23', '54']),
    (' 10,230,540', ['10,230,540']),
    (' {10.0}, {20}', ['10.0', '20']),
    (' 2015.', ['2015']),
])
def test_find_numeric_values(text, expected):
    assert find_numeric_values(text) == expected


@pytest.mark.parametrize('text, expected_references, expected_unreferenced', [
    (r'The number 1.2 is a numeric value.', [], ['1.2']),
    (r'The numbers \hyperlink{A0}{1.2e-3} and \hyperlink{A1}{-7.8}.',
     [ReferencedValue(value='1.2e-3', label='A0', is_target=False),
      ReferencedValue(value='-7.8', label='A1', is_target=False)], []),
    (r'The numbers \hyperlink{A0}{1.2e-3} and -7.8.',
     [ReferencedValue(value='1.2e-3', label='A0', is_target=False)], ['-7.8']),
    (r'The numbers \num{\hyperlink{A0}{1.2e-3} + 3} and -7.8.',
     [ReferencedValue(value='1.2e-3', label='A0', is_target=False)], ['3', '-7.8']),
])
def test_find_referenced_and_unreferenced_numeric_values(text, expected_references, expected_unreferenced):
    assert find_hyperlinks(text) == expected_references
    assert find_numeric_values(text, remove_hyperlinks=True) == expected_unreferenced


@pytest.mark.parametrize('value, expected_value, expected_is_percent', [
    ('1.2', '1.2', False),
    ('1.2e-3', '1.2e-3', False),
    ('+1.2e-3', '+1.2e-3', False),
    ('-12', '-12', False),
    ('--12', None, False),
    ('a', None, False),
    ('1.2a', None, False),
    ('1.2e-3a', None, False),
    ('28.4', '28.4', False),
    ('28.4%', '28.4', True),
    ('28.4 %', '28.4', True),
    (r'28.4\%', '28.4', True),
    (r'28.4 \%', '28.4', True),
    ('28.4%%', None, False),
    ('28.4  %', None, False),
    ('28.4a', None, False),
    ('aaa', None, False),
])
def test_referenced_value_get_numeric_and_is_percent(value, expected_value, expected_is_percent):
    assert ReferencedValue(value=value).get_numeric_value_and_is_percent() == (expected_value, expected_is_percent)
