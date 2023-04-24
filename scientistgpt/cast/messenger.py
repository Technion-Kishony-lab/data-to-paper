from dataclasses import dataclass, field
from typing import List, Optional, Union

from scientistgpt.conversation import Conversation
from scientistgpt.utils.singleton import Singleton

from .cast import Agent
from ..conversation.actions import Action


@dataclass
class Messenger(metaclass=Singleton):
    """
    A first-person messaging app.
    """
    first_person: Agent = Agent.Student
    contacts: List[Agent] = field(default_factory=list)
    conversations: List[Conversation] = field(default_factory=list)

    def add_contact(self, agent: Agent):
        if agent not in self.contacts:
            self.contacts.append(agent)

    def add_contacts(self, agents: Optional[List[Agent]] = None):
        """
        Add specified agents to contact. If no agents are specified, add all agents except the Student.
        """
        if agents is None:
            agents = [agent for agent in Agent if agent != self.first_person]
        for agent in agents:
            self.add_contact(agent)

    def remove_contact(self, agent: Agent):
        if agent in self.contacts:
            self.contacts.remove(agent)

    def add_conversation(self, conversation: Conversation):
        """
        Add a conversation to the messenger.
        The conversation must include the first_person.
        """
        assert self.first_person in conversation.participants
        self.conversations.append(conversation)
        for agent in conversation.participants:
            self.add_contact(agent)

    def remove_conversation(self, conversation: Conversation):
        self.conversations.remove(conversation)

    def on_action(self, action: Action):
        pass


ALL_MESSENGERS: List[Messenger] = []


def create_messenger(first_person: Agent, contacts: Optional[List[Agent]] = None) -> Messenger:
    messenger = Messenger(first_person=first_person)
    messenger.add_contacts(contacts)
    ALL_MESSENGERS.append(messenger)
    return messenger


STUDENT_MESSENGER = create_messenger(first_person=Agent.Student)
