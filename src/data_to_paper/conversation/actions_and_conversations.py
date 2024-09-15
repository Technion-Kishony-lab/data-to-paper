"""
This file contains the primary list of actions and the dict of conversations.

The action list allows a formal record of all the actions that were performed on the conversations.
Using the actions, we can replay the entire conversation history.

The dict of conversations is used to keep track of conversations by name, as they are created and modified by actions.
"""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import Union, Dict, List, Optional, Set
from dataclasses import dataclass, field

from data_to_paper.utils.print_to_file import print_and_log
from data_to_paper.base_cast import Agent
from .conversation import Conversation


@dataclass(frozen=True)
class Action:
    """
    Base class for actions performed on a Conversation, Stage, or Cast.
    """
    should_print: bool = True

    def _pretty_attrs(self) -> str:
        return ''

    def pretty_repr(self, is_color: bool = True) -> str:
        s = ''
        s += f'{type(self).__name__}'
        if self._pretty_attrs():
            s += f'({self._pretty_attrs()})'
        return s

    def apply(self):
        """
        Apply the action.
        """
        pass


@dataclass(frozen=True)
class Conversations(Dict[str, Conversation]):
    """
    a dict containing all managed conversations, by name.
    """

    def get_conversation(self, conversation_name: str) -> Optional[Conversation]:
        """
        Return the conversation with the provided name, or None if no such conversation exists.
        """
        return self.get(conversation_name, None)

    def get_or_create_conversation(self, conversation_name: str, participants: Set[Agent] = None) -> Conversation:
        if conversation_name in self:
            return self[conversation_name]
        conversation = Conversation(conversation_name=conversation_name, participants=participants)
        self[conversation.conversation_name] = conversation
        return conversation

    def get_new_conversation_name(self, prefix: str = 'conversation') -> str:
        """
        Return a new conversation name that is not already in use.
        """
        i = 0
        while True:
            conversation_name = f'{prefix} ({i})'
            if conversation_name not in self:
                return conversation_name
            i += 1


@dataclass(frozen=True)
class Actions(List[Action]):
    """
    a list of actions applied to conversations by order in which actions were applied.
    """

    abbreviate_repeated_printed_content: bool = True

    def apply_action(self, action: Action, is_color: bool = True,
                     should_append: bool = True):
        if action.should_print:
            from .conversation_actions import AppendMessage
            if self.abbreviate_repeated_printed_content \
                    and isinstance(action, AppendMessage) \
                    and action.message.content in self.get_all_message_contents(only_printed=True):
                s = action.pretty_repr(is_color=is_color, abbreviate_content=True)
                s_bw = action.pretty_repr(is_color=False, abbreviate_content=True)
            else:
                s = action.pretty_repr(is_color=is_color)
                s_bw = action.pretty_repr(is_color=False)
            if s:
                print_and_log(s_bw, text_in_color=s, end='\n\n')
        if should_append:
            self.append(action)
        action.apply()

    def save_actions_to_file(self, file_path: Union[str, Path]):
        """
        Save the primary list of actions to a json file.
        """
        with open(file_path, 'wb') as f:
            pickle.dump(self, f)

    def load_actions_from_file(self, file_path: Union[str, Path]):
        """
        Load a list of actions from a json file.
        """
        with open(file_path, 'rb') as f:
            self.clear()
            self.extend(pickle.load(f))
        return self

    def get_actions_for_conversation(self, conversation_name: str) -> List[Action]:
        """
        Return a list of actions that were applied to the conversation with the provided name.
        """
        from .conversation_actions import ChangeMessagesConversationAction
        return [action for action in self if
                isinstance(action, ChangeMessagesConversationAction) and action.conversation_name == conversation_name]

    def get_all_message_contents(self, only_printed: bool = False) -> List[str]:
        """
        Return a list of all message contents.
        """
        from .conversation_actions import AppendMessage
        return [action.message.content for action in self
                if isinstance(action, AppendMessage) and (not only_printed or
                                                          (action.should_print and
                                                           action.should_add_to_conversation()))
                ]


@dataclass(frozen=True)
class ActionsAndConversations:
    actions: Actions = field(default_factory=Actions)
    conversations: Conversations = field(default_factory=Conversations)
