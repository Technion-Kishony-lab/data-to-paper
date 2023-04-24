from unittest.mock import Mock

from scientistgpt import Conversation
from scientistgpt.cast import Agent
from scientistgpt.cast.messenger import Messenger


def test_messanger_add_remove_contact():
    messanger = Messenger()
    agent = Agent.Mentor
    messanger.add_contact(agent)
    assert agent in messanger.contacts
    messanger.remove_contact(agent)
    assert agent not in messanger.contacts


def test_messanger_add_delete_conversation():
    messanger = Messenger()
    conversation = Conversation(participants=[Agent.Mentor, Agent.Student])
    messanger.add_conversation(conversation)
    assert len(messanger.conversations) == 1
    messanger.remove_conversation(conversation)
    assert len(messanger.conversations) == 0


def test_messanger_is_singleton():
    messanger1 = Messenger()
    messanger2 = Messenger()
    assert messanger1 is messanger2
