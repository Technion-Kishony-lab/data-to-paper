import pytest

from scientistgpt.utils import dedent_triple_quote_str
from scientistgpt.utils.text_extractors import extract_text_between_tags, extract_to_nearest_space, \
    get_formatted_sections, convert_formatted_sections_to_text

text_1 = 'hello, here is a list [1, 2, 3, [4], 5] of numbers and lists'

text_2 = '\\title{\\textbf{this is some title in bold}} \n' \
         '\\start{abstract} this is also the abstract \\end{abstract}'

text_3 = '\\section{Introduction} \n' \
         'this is the introduction \n'


@pytest.mark.parametrize('text, start_tag, end_tag, leave_tags, expected', [
    (text_1, '[', ']', False, '1, 2, 3, [4], 5'),
    (text_1, '[', ']', True, '[1, 2, 3, [4], 5]'),
    (text_2, '\\title{', '}', False, '\\textbf{this is some title in bold}'),
    (text_2, '\\title{', '}', True, '\\title{\\textbf{this is some title in bold}}'),
    (text_2, '\\start{abstract}', '\\end{abstract}', False, ' this is also the abstract '),
    (text_1, '[', None, False, '1, 2, 3, [4], 5] of numbers and lists'),
    (text_1, '[', None, True, '[1, 2, 3, [4], 5] of numbers and lists'),
    (text_3, '\\section{Introduction}', None, False, ' \nthis is the introduction \n'),
    ('here is a """tripple-quoted text""".', '"""', '"""', False, 'tripple-quoted text'),
])
def test_extract_text_between_tags(text, start_tag, end_tag, leave_tags, expected):
    assert extract_text_between_tags(text, start_tag, end_tag, leave_tags) == expected


def test_extract_to_nearest_space():
    text = 'This is a test text to test the extract_to_nearest_space function.'
    assert extract_to_nearest_space(text, 18) == 'This is a test'
    assert extract_to_nearest_space(text, 200) == text
    assert extract_to_nearest_space(text, -13) == 'function.'
    assert extract_to_nearest_space(text, 3) == 'Thi'
    assert extract_to_nearest_space(text, -4) == 'ion.'


@pytest.mark.parametrize('text, label, is_complete, assembled_to', [
    ('hello', None, True, None),
    ("```python\na = 2\n```", 'python', True, None),
    ("``` python\na = 2\n```", 'python', True, "```python\na = 2\n```"),
    ("```python \na = 2\n```", 'python', True, "```python\na = 2\n```"),
    ("```\na = 2\n```", '', True, None),
    ("```\na = 2\n", '', False, None),
])
def test_split_text_by_triple_backticks(text, label, is_complete, assembled_to):
    labels_sections_complete = get_formatted_sections(text)
    assembled_to = assembled_to or text
    print(labels_sections_complete)
    assert labels_sections_complete[0].label == label
    assert labels_sections_complete[0].is_complete == is_complete
    assert convert_formatted_sections_to_text(labels_sections_complete) == assembled_to
