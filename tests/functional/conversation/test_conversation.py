import os.path

import openai
import pytest

from data_to_paper import Conversation, Message, Role
from data_to_paper.servers.llm_call import OPENAI_SERVER_CALLER, try_get_llm_response, \
    count_number_of_tokens_in_message
from data_to_paper.servers.model_engine import ModelEngine


@pytest.mark.parametrize('text, expected', [
    ("10", 1),
    ("hypertarget", 3),
    ("hyperlink", 2),
    ("ref", 1),
    (r"\hypertarget{C37}{10}", 10),
    ("refC37{10}", 6),
    ("hypertarget_C37{10}", 8),
    ("10refC37", 4),
    ("10hypertarget_C37", 6),
])
def test_count_number_of_tokens_in_message(text, expected):
    for model_engine in [ModelEngine.GPT4, ModelEngine.GPT4_TURBO]:
        assert count_number_of_tokens_in_message(text, model_engine) == expected


def test_failed_gpt_response(conversation, openai_exception):
    with OPENAI_SERVER_CALLER.mock(['I am okay.', openai_exception]):
        assert try_get_llm_response(conversation) == 'I am okay.'
        assert isinstance(try_get_llm_response(conversation), openai.error.InvalidRequestError)


@OPENAI_SERVER_CALLER.record_or_replay()
def test_conversation_gpt_response(conversation):
    response = try_get_llm_response(conversation)
    assert isinstance(response, str) and len(response)


@OPENAI_SERVER_CALLER.record_or_replay()
def test_conversation_gpt_response_without_appending(conversation):
    response = try_get_llm_response(conversation)
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
    conversation.append(Message(Role.ASSISTANT, 'Hello!'))
    assert conversation.get_last_response() == 'Hello!'


def test_conversation_delete_last_response(conversation):
    conversation.append(Message(Role.ASSISTANT, 'Hello!'))
    original_len = len(conversation)
    conversation.delete_last_response()
    assert len(conversation) == original_len - 1


def test_conversation_ignores_ignored_messages():
    conversation = Conversation()
    conversation.append(Message(Role.USER,
                                'This is a fun message just for the conversation to look nice!', ignore=True))
    conversation.append(Message(Role.USER, 'This is a real message', ignore=False))
    indices_and_messages = conversation.get_chosen_indices_and_messages()
    indices = [index for index, _ in indices_and_messages]
    assert indices == [1]
