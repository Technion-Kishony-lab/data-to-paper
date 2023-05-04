from unittest.mock import Mock

from g3pt import Conversation
from g3pt.cast import Agent
from g3pt.cast.messenger import Messenger, create_messenger
from g3pt.conversation.actions import CreateConversation, apply_action


def test_messenger_add_remove_contact():
    messenger = Messenger()
    agent = Agent.Mentor
    messenger.add_contact(agent)
    assert agent in messenger.contacts
    messenger.remove_contact(agent)
    assert agent not in messenger.contacts


def test_messenger_add_delete_conversation():
    messenger = Messenger()
    conversation = Conversation(participants=[Agent.Mentor, Agent.Student])
    messenger.add_conversation(conversation)
    assert len(messenger.conversations) == 1
    messenger.remove_conversation(conversation)
    assert len(messenger.conversations) == 0


def test_messenger_on_action():
    messenger = create_messenger(first_person=Agent.Secretary)
    messenger.on_action = Mock()
    messenger.tag = 'test'
    action = CreateConversation(participants={Agent.Secretary, Agent.Mentor})
    apply_action(action)
    messenger.on_action.assert_called_once()
