from unittest.mock import Mock

from scientistgpt import Conversation
from scientistgpt.base_cast import Agent
from scientistgpt.base_cast.messenger import Messenger, create_messenger
from scientistgpt.conversation.actions import apply_action
from scientistgpt.conversation.conversation_actions import CreateConversation


class TestAgent(Agent):
    GOOD_AGENT = 'good_agent'
    BAD_AGENT = 'bad_agent'


def test_messenger_add_remove_contact():
    messenger = Messenger(first_person=TestAgent.GOOD_AGENT)
    agent = TestAgent.BAD_AGENT
    messenger.add_contact(agent)
    assert agent in messenger.contacts
    messenger.remove_contact(agent)
    assert agent not in messenger.contacts


def test_messenger_add_delete_conversation():
    messenger = Messenger(first_person=TestAgent.GOOD_AGENT)
    conversation = Conversation(participants=[TestAgent.GOOD_AGENT, TestAgent.BAD_AGENT])
    messenger.add_conversation(conversation)
    assert len(messenger.conversations) == 1
    messenger.remove_conversation(conversation)
    assert len(messenger.conversations) == 0


def test_messenger_on_action():
    messenger = create_messenger(first_person=TestAgent.GOOD_AGENT)
    messenger.on_action = Mock()
    messenger.tag = 'test'
    action = CreateConversation(participants={TestAgent.GOOD_AGENT, TestAgent.BAD_AGENT},
                                web_conversation_name='web_test')
    apply_action(action)
    messenger.on_action.assert_called_once()
