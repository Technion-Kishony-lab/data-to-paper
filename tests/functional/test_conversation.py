from _pytest.fixtures import fixture

from scientistgtp import Conversation, Role


@fixture()
def conversation():
    conversation = Conversation()
    conversation.append_message(Role.SYSTEM, 'You are a helpful assistant.')
    conversation.append_message(Role.USER, 'How are you?')
    return conversation


def test_conversation_gpt_response(conversation):
    assert len(conversation) == 2, "sanity"
    response = conversation.get_response_from_chatgpt(should_print=False, should_append=True)
    assert len(response)
    assert len(conversation) == 3


def test_conversation_gpt_response_without_appending(conversation):
    response = conversation.get_response_from_chatgpt(should_print=False, should_append=False)
    assert len(response)
    assert len(conversation) == 2
