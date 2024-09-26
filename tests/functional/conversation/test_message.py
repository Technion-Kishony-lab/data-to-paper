import colorama
import pytest
from pytest import fixture

from data_to_paper import Role, Message
from data_to_paper.text.highlighted_text import python_to_highlighted_text


@fixture()
def message_with_tag():
    return Message(Role.USER, 'Hi there!', 'first')


@fixture()
def message_without_tag():
    return Message(Role.USER, 'Hello')


@pytest.mark.parametrize('is_color', [
    True, False,
])
def test_message_display(message_with_tag, is_color):
    s = message_with_tag.pretty_repr(731, is_color=is_color)
    print()
    print(s)
    assert message_with_tag.role.name in s
    assert message_with_tag.content in s
    assert message_with_tag.tag in s
    assert '731' in s


def test_message_save_to_text(message_with_tag):
    assert Message.from_text(message_with_tag.convert_to_text()) == message_with_tag


def test_message_save_to_text_no_tag(message_without_tag):
    assert Message.from_text(message_without_tag.convert_to_text()) == message_without_tag


def test_message_convert_to_chatgpt(message_with_tag):
    assert message_with_tag.to_llm_dict() == {'role': 'user', 'content': 'Hi there!'}


def test_message_repr_with_code_and_non_code_blocks():
    message = Message(Role.USER, "Here is my hello world code:\n\n```python\nprint('hello')\n```\n\nIt produces: "
                                 "```\nhello\n```\n\nThat's all folks!")
    pretty = message.pretty_content(text_color=colorama.Fore.CYAN, width=100)
    assert colorama.Fore.LIGHTCYAN_EX in pretty
    assert python_to_highlighted_text("print('hello')", color=colorama.Fore.CYAN)[:-1] in pretty
