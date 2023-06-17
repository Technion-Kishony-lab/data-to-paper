import pytest

from data_to_paper.conversation.message_designation import SingleMessageDesignation, RangeMessageDesignation, \
    convert_general_message_designation_to_int_list


def test_single_message_designation(conversation):
    d = SingleMessageDesignation('code')
    assert str(d) == '<code>'
    assert d.get_message_nums(conversation) == [2]

    d = SingleMessageDesignation('code', 1)
    assert str(d) == '<code +1>'
    assert d.get_message_nums(conversation) == [3]


@pytest.mark.parametrize('start, end, expected', [
    (1, 3, [1, 2, 3]),
    (None, 'code', [0, 1, 2]),
    (None, SingleMessageDesignation('code', 1), [0, 1, 2, 3]),
])
def test_range_message_designation(conversation, start, end, expected):
    assert RangeMessageDesignation.from_(start, end).get_message_nums(conversation) == expected


@pytest.mark.parametrize('start, end, expected', [
    (1, 3, '<1> - <3>'),
    (None, 'code', '<0> - <code>'),
    (None, SingleMessageDesignation('code', 1), '<0> - <code +1>'),
])
def test_range_message_designation_repr(start, end, expected):
    assert str(RangeMessageDesignation.from_(start, end)) == expected


@pytest.mark.parametrize('designations, expected', [
    ([1, 'code'], [1, 2]),
    ([1, 'code', -1], [1, 2, 3]),
    ('code', [2]),
    (None, []),
    (-1, [3]),
    (SingleMessageDesignation('code', 1), [3]),
])
def test_convert_general_message_designation_to_int_list(conversation, designations, expected):
    assert convert_general_message_designation_to_int_list(designations, conversation) == expected
