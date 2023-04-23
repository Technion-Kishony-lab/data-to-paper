from scientistgpt.utils import extract_text_between_tags

text = 'hello, here is a list [1, 2, 3, [4], 5] of numbers and lists'


def test_extract_text_between_tags():
    assert extract_text_between_tags(text, '[', ']') == '1, 2, 3, [4], 5'
    assert extract_text_between_tags(text, '[', ']', leave_tags=True) == '[1, 2, 3, [4], 5]'


def test_extract_text_between_tags_open_ended():
    assert extract_text_between_tags(text, '[', None) == '1, 2, 3, [4], 5] of numbers and lists'
    assert extract_text_between_tags(text, '[', None, leave_tags=True) == '[1, 2, 3, [4], 5] of numbers and lists'
