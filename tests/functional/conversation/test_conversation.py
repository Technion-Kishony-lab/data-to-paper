import os.path

from _pytest.fixtures import fixture

from scientistgpt import Conversation, Role, Message


def test_conversation_gpt_response(conversation):
    response = conversation.try_get_chatgpt_response()
    assert isinstance(response, str) and len(response)


def test_conversation_gpt_response_without_appending(conversation):
    response = conversation.try_get_chatgpt_response()
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


def test_conversation_print(conversation):
    conversation.print_all_messages()


def test_conversation_get_last_response(conversation):
    conversation.append_assistant_message('Hello!')
    assert conversation.get_last_response() == 'Hello!'


def test_conversation_delete_last_response(conversation):
    conversation.append_assistant_message('Hello!')
    original_len = len(conversation)
    conversation.delete_last_response()
    assert len(conversation) == original_len - 1
