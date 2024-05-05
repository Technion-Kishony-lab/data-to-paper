from __future__ import annotations

import re

from typing import List, Tuple, Optional, Set

from data_to_paper.utils.tag_pairs import SAVE_TAGS

from .message import Message, Role
from .message_designation import GeneralMessageDesignation, convert_general_message_designation_to_int_list

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from data_to_paper.base_cast import Agent


class Conversation(List[Message]):
    """
    Maintain a list of messages as exchanged between USER and ASSISTANT.

    Takes care of:

    1. save/load to text.
    2. print colored-styled messages.

    DO NOT ALTER CONVERSATION INSTANCE DIRECTLY. USE `ConversationManager` INSTEAD.
    """

    def __init__(self, *args, conversation_name: Optional[str] = None,
                 participants: Optional[Set[Agent]] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.conversation_name = conversation_name
        self.participants = participants  # None - do not enforce participants

    def add_participant(self, agent: Agent):
        if self.participants is None:
            self.participants = []
        self.participants.add(agent)

    def remove_participant(self, agent: Agent):
        if self.participants is not None:
            self.participants.remove(agent)

    def get_other_participant(self, agent: Agent) -> Agent:
        if len(self.participants) != 2:
            raise ValueError('Conversation must have exactly two participants.')
        for participant in self.participants:
            if participant is not agent:
                return participant

    def append(self, message: Message):
        if self.participants is not None and message.role is not Role.COMMENTER:
            assert message.agent in self.participants, f'Agent {message.agent} not in conversation participants.'
        super().append(message)

    def get_chosen_indices_and_messages(self, hidden_messages: GeneralMessageDesignation = None
                                        ) -> List[Tuple[int, Message]]:
        """
        Return sub-list of messages.
        Remove commenter messages, ignore=True messages, as well as all messages indicated in `hidden_messages`.
        """
        hidden_messages = hidden_messages or []
        hidden_messages = convert_general_message_designation_to_int_list(hidden_messages, self)
        return [(i, message) for i, message in enumerate(self)
                if i not in hidden_messages
                and message.role is not Role.COMMENTER
                and not message.ignore]

    def get_chosen_messages(self, hidden_messages: GeneralMessageDesignation = None) -> List[Message]:
        """
        Return sub-list of messages.
        Remove commenter messages, ignore=True messages, as well as all messages indicated in `hidden_messages`.
        """
        return [message for _, message in self.get_chosen_indices_and_messages(hidden_messages)]

    def get_last_response(self) -> str:
        """
        Return the last response from the assistant.

        will skip over any COMMENTER messages.
        """
        last_non_commenter_message = self.get_last_non_commenter_message()
        if not last_non_commenter_message.role.is_assistant_or_surrogate():
            raise ValueError('Last message is not an assistant response.')
        return last_non_commenter_message.content

    def get_last_non_commenter_message(self) -> Message:
        """
        Return the last non-commenter message.
        """
        for i in range(len(self) - 1, -1, -1):
            if self[i].role is not Role.COMMENTER:
                return self[i]
        raise ValueError('No non-commenter message found.')

    def get_message_index_by_tag(self, tag):
        for i, message in enumerate(self):
            if message.tag == tag:
                return i
        raise ValueError(f'Tag {tag} not found.')

    def save(self, filename: str):
        with open(filename, 'w') as f:
            for message in self:
                f.write(SAVE_TAGS.wrap(message.convert_to_text()) + '\n\n')

    def load(self, filename: str):
        self.clear()
        with open(filename, 'r') as f:
            entire_file = f.read()
            matches = re.findall(SAVE_TAGS.wrap("(.*?)"), entire_file, re.DOTALL)
            for match in matches:
                self.append(Message.from_text(match))

    @classmethod
    def from_file(cls, filename: str):
        self = cls()
        self.load(filename)
        return self

    def print_all_messages(self):
        for message in self:
            print(message.pretty_repr())
            print()
