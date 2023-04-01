import os.path

from _pytest.fixtures import fixture

from scientistgpt import Conversation, Role


@fixture()
def conversation():
    conversation = Conversation()
    conversation.append_message(Role.SYSTEM, 'You are a helpful assistant.')
    conversation.append_user_message('Write a short code.')
    conversation.append_assistant_message('Here is my code:\n\n'
                                          '```python\n'
                                          'print(7)\n'
                                          '```\n')
    conversation.append_user_message('How are you?')
    return conversation


def test_conversation_gpt_response(conversation):
    assert len(conversation) == 4, "sanity"
    response = conversation.get_response_from_chatgpt(should_print=False, should_append=True)
    assert len(response)
    assert len(conversation) == 5


def test_conversation_gpt_response_without_appending(conversation):
    response = conversation.get_response_from_chatgpt(should_print=False, should_append=False)
    assert len(response)
    assert len(conversation) == 4


def test_conversation_save_load(conversation, tmpdir):
    filename = os.path.join(tmpdir, 'test_conversation_save.txt')
    conversation.save(filename)
    new_conversation = Conversation()
    new_conversation.load(filename)

    assert new_conversation == conversation


def test_conversation_from_file(conversation, tmpdir):
    filename = os.path.join(tmpdir, 'test_conversation_save.txt')
    conversation.save(filename)
    new_conversation = Conversation.from_file(filename)

    assert new_conversation == conversation
