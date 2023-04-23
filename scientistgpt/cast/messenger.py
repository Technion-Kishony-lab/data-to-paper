from dataclasses import dataclass, field
from typing import List, Optional

from scientistgpt.conversation import Conversation
from scientistgpt.utils.singleton import Singleton

from .cast import Agent


@dataclass
class ConversationSetup:
    """
    Properties of a conversation in the Student's messaging app.
    """
    name: str = ''
    participants: List[Agent] = field(default_factory=list)
    conversation: Conversation = None
    is_group: bool = False  # if False, the conversation is a one-on-one conversation with the Student


@dataclass
class Messenger(metaclass=Singleton):
    """
    A first-person view of the Student's messaging app.
    """
    first_person: Agent = Agent.STUDENT
    contacts: List[Agent] = field(default_factory=list)
    conversation_setups: List[ConversationSetup] = field(default_factory=list)

    def add_contact(self, agent: Agent):
        if agent not in self.contacts:
            self.contacts.append(agent)

    def add_contacts(self, agents: Optional[List[Agent]] = None):
        """
        Add specified agents to contact. If no agents are specified, add all agents except the Student.
        """
        if agents is None:
            agents = [agent for agent in Agent if agent != Agent.STUDENT]
        for agent in agents:
            self.add_contact(agent)

    def remove_contact(self, agent: Agent):
        if agent in self.contacts:
            self.contacts.remove(agent)

    def create_conversation(self, conversation_name: str, participants: List[Agent], conversation: Conversation):
        self.conversation_setups.append(
            ConversationSetup(name=conversation_name, participants=participants, conversation=conversation))
        for agent in participants:
            self.add_contact(agent)

    def delete_conversation(self, conversation_name: str):
        for i, conversation_setup in enumerate(self.conversation_setups):
            if conversation_setup.name == conversation_name:
                self.conversation_setups.pop(i)

    def add_participant_to_conversation(self, conversation_name: str, agent: Agent):
        for conversation_setup in self.conversation_setups:
            if conversation_setup.name == conversation_name:
                conversation_setup.participants.append(agent)
                self.add_contact(agent)

    def remove_participant_from_conversation(self, conversation_name: str, agent: Agent):
        for conversation_setup in self.conversation_setups:
            if conversation_setup.name == conversation_name:
                conversation_setup.participants.remove(agent)


MESSENGER = Messenger()
