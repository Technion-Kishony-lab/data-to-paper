import openai
from _pytest.fixtures import fixture

from data_to_paper import Role, Message
from data_to_paper.servers.chatgpt import OPENAI_MAX_CONTENT_LENGTH_MESSAGE_CONTAINS


@fixture()
def conversation(conversations):
    conversation = conversations.get_or_create_conversation(conversation_name='default')
    conversation.append(Message(Role.SYSTEM, 'You are a helpful assistant.'))
    conversation.append(Message(Role.USER, 'Write a short code.', 'write_code'))
    conversation.append(Message(Role.ASSISTANT, 'Here is my code:\n\n'
                                                '```python\n'
                                                'print(7)\n'
                                                '```\n', 'code'))
    conversation.append(Message(Role.USER, 'How are you?'))
    return conversation


@fixture()
def openai_exception():
    return openai.error.InvalidRequestError(param='prompt', message=OPENAI_MAX_CONTENT_LENGTH_MESSAGE_CONTAINS)
