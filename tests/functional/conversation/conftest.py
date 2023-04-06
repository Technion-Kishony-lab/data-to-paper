from _pytest.fixtures import fixture

from scientistgpt import Conversation, Role, Message


@fixture()
def conversation():
    conversation = Conversation()
    conversation.append(Message(Role.SYSTEM, 'You are a helpful assistant.'))
    conversation.append(Message(Role.USER, 'Write a short code.'))
    conversation.append_assistant_message('Here is my code:\n\n'
                                          '```python\n'
                                          'print(7)\n'
                                          '```\n')
    conversation.append_user_message('How are you?')
    return conversation


