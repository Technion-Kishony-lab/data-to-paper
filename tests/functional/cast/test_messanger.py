from scientistgpt.cast import Agent
from scientistgpt.cast.messenger import Messenger


def test_messanger_add_remove_contact():
    messanger = Messenger()
    agent = Agent.Mentor
    messanger.add_contact(agent)
    assert agent in messanger.contacts
    messanger.remove_contact(agent)
    assert agent not in messanger.contacts


def test_messanger_create_delete_conversation():
    messanger = Messenger()
    conversation_name = 'test'
    participants = [Agent.Mentor]
    messanger.create_conversation(conversation_name, participants, None)
    assert len(messanger.conversation_setups) == 1
    messanger.delete_conversation(conversation_name)
    assert len(messanger.conversation_setups) == 0


def test_messanger_add_remove_participant():
    messanger = Messenger()
    conversation_name = 'test'
    participants = [Agent.Mentor]
    messanger.create_conversation(conversation_name, participants, None)
    agent = Agent.Student
    messanger.add_participant_to_conversation(conversation_name, agent)
    assert agent in messanger.conversation_setups[0].participants
    messanger.remove_participant_from_conversation(conversation_name, agent)
    assert agent not in messanger.conversation_setups[0].participants


def test_messanger_is_singleton():
    messanger1 = Messenger()
    messanger2 = Messenger()
    assert messanger1 is messanger2
