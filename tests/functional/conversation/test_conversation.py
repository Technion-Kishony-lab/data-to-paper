import os.path

import openai

from scientistgpt import Conversation
from tests.utils import mock_openai, record_or_replay_openai


def test_failed_gpt_response(conversation, openai_exception):
    with mock_openai(['I am okay.',
                      openai_exception,
                      ]):
        assert conversation.try_get_chatgpt_response() == 'I am okay.'
        assert isinstance(conversation.try_get_chatgpt_response(), openai.error.InvalidRequestError)


@record_or_replay_openai()
def test_conversation_gpt_response(conversation):
    response = conversation.try_get_chatgpt_response()
    assert isinstance(response, str) and len(response)


@record_or_replay_openai()
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


def test_conversation_get_message_content_by_tag(conversation):
    conversation.append_assistant_message('Hello!', tag='hello')
    assert conversation.get_message_content_by_tag('hello') == 'Hello!'
    assert conversation.get_message_content_by_tag('not-hello') is None
