from dataclasses import dataclass, field
from typing import List, Optional

from scientistgpt.conversation import Conversation
from scientistgpt.conversation.actions import Action

from .cast import Agent


@dataclass
class Messenger:
    """
    A first-person messaging app.
    """
    first_person: Agent = Agent.Student
    contacts: List[Agent] = field(default_factory=list)
    conversations: List[Conversation] = field(default_factory=list)

    #
    def __post_init__(self):
        ALL_MESSENGERS.append(self)


    # @classmethod
    # def create(cls, *args, **kwargs):
    #     self = cls(*args, **kwargs)
    #     ALL_MESSENGERS.append(self)
    #     return self

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
        """
        Called after an action was applied to a conversation managed by this messenger.
        """
        if action.conversation not in self.conversations:
            self.add_conversation(action.conversation)
        self._update_on_action(action)

    def _update_on_action(self, action: Action):
        """
        a hook to update the front-end on an action.
        ORI + MAOR
        """
        pass


ALL_MESSENGERS: List[Messenger] = []


def create_messenger(first_person: Agent, contacts: Optional[List[Agent]] = None) -> Messenger:
    messenger = Messenger(first_person=first_person)
    messenger.add_contacts(contacts)
    return messenger


def on_action(action: Action):
    for messenger in ALL_MESSENGERS:
        if messenger.first_person in action.conversation.participants:
            messenger.on_action(action)


# STUDENT_MESSENGER = create_messenger(first_person=Agent.Student)
