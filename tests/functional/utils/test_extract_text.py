import pytest

from data_to_paper.text.text_extractors import extract_text_between_tags, extract_to_nearest_space, \
    extract_all_external_brackets

text_1 = 'hello, here is a list [1, 2, 3, [4], 5] of numbers and lists'

text_2 = '\\title{\\textbf{this is some title in bold}} \n' \
         '\\start{abstract} this is also the abstract \\end{abstract}'

text_3 = '\\section{Introduction} \n' \
         'this is the introduction \n'

text_4 = 'hello [world [inner]], what is your [name]'
text_5 = 'hello [world [inner]], what is your [name'


@pytest.mark.parametrize('text, start_tag, end_tag, keep_tags, expected', [
    (text_1, '[', ']', False, '1, 2, 3, [4], 5'),
    (text_1, '[', ']', True, '[1, 2, 3, [4], 5]'),
    (text_2, '\\title{', '}', False, '\\textbf{this is some title in bold}'),
    (text_2, '\\title{', '}', True, '\\title{\\textbf{this is some title in bold}}'),
    (text_2, '\\start{', '}', True, '\\start{abstract}'),
    (text_2, '\\start{abstract}', '\\end{abstract}', False, ' this is also the abstract '),
    (text_1, '[', None, False, '1, 2, 3, [4], 5] of numbers and lists'),
    (text_1, '[', None, True, '[1, 2, 3, [4], 5] of numbers and lists'),
    (text_3, '\\section{Introduction}', None, False, ' \nthis is the introduction \n'),
    ('here is a """tripple-quoted text""".', '"""', '"""', False, 'tripple-quoted text'),
])
def test_extract_text_between_tags(text, start_tag, end_tag, keep_tags, expected):
    assert extract_text_between_tags(text, start_tag, end_tag, keep_tags) == expected


@pytest.mark.parametrize('text, start_tag, expected', [
    (text_1, '[', ['[1, 2, 3, [4], 5]']),
    (text_4, '[', ['[world [inner]]', '[name]']),
    (text_5, '[', ['[world [inner]]']),
    ("'hello [world [inner] [inner2]], what is your [name]'", '[', ["[world [inner] [inner2]]", "[name]"]),
    ("I have /num{1+2} apples.", '/num{', ['/num{1+2}']),
    ("I have /num{/hyperlink{a}{1}+2} apples.", '/num{', ['/num{/hyperlink{a}{1}+2}']),
    ("I have /num{/hyperlink{a}{1}+2} apples and /num{3} bananas.", '/num{', ['/num{/hyperlink{a}{1}+2}', '/num{3}']),
])
def test_extract_all_external_brackets(text, start_tag, expected):
    assert extract_all_external_brackets(text, start_tag[-1], None, open_phrase=start_tag) == expected


def test_extract_all_external_brackets_with_open_phrase():
    text = r"I have /num{/hypoerlink{a}{1}+2} apples and /num{3} bananas and {77} oranges."
    assert extract_all_external_brackets(text, '{', open_phrase=r'/num{') == ['/num{/hypoerlink{a}{1}+2}', '/num{3}']


def test_extract_to_nearest_space():
    text = 'This is a test text to test the extract_to_nearest_space function.'
    assert extract_to_nearest_space(text, 18) == 'This is a test'
    assert extract_to_nearest_space(text, 200) == text
    assert extract_to_nearest_space(text, -13) == 'function.'
    assert extract_to_nearest_space(text, 3) == 'Thi'
    assert extract_to_nearest_space(text, -4) == 'ion.'
