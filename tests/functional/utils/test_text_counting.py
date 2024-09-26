import pytest

from data_to_paper.text.text_counting import diff_strs


@pytest.mark.parametrize('context, expected', [
    (0, ' ... (f) [1] [2] [3]  ... '),
    (1, ' ... e (f) [1] [2] [3] g  ... '),
    (2, ' ... d e (f) [1] [2] [3] g h  ... '),
])
def test_diff_strs(context, expected):
    str1 = 'a b c d e f g h i j'
    str2 = 'a b c d e 1 2 3 g h i j'

    assert diff_strs(str1, str2, context=context, add_template='[{}] ', remove_template='({}) ') \
           == expected
