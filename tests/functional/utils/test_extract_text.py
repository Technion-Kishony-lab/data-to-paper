import pytest

from scientistgpt.utils import extract_text_between_tags

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
])
def test_extract_text_between_tags(text, start_tag, end_tag, leave_tags, expected):
    assert extract_text_between_tags(text, start_tag, end_tag, leave_tags) == expected
