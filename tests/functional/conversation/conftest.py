import openai
from _pytest.fixtures import fixture

from scientistgpt import Conversation, Role, Message
from scientistgpt.conversation.store_conversations import get_or_create_conversation


@fixture()
def conversation():
    conversation = get_or_create_conversation(conversation_name='default')
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
    return openai.error.InvalidRequestError(param='prompt', message='The prompt must be a string.')
