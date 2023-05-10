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

from .conversation import Conversation, WebConversation
from scientistgpt.base_cast import Agent


@dataclass(frozen=True)
class Action:
    """
    Base class for actions performed on a Conversation, Stage, or Cast.
    """

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

    def apply_to_web(self) -> bool:
        return False


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

    def get_or_create_conversation(self, conversation_name: str, participants: Set[Agent] = None, is_web: bool = False
                                   ) -> Conversation:
        if conversation_name in self:
            return self[conversation_name]
        conversation = Conversation(conversation_name=conversation_name, participants=participants) if not is_web \
            else WebConversation(conversation_name=conversation_name, participants=participants)
        self[conversation.conversation_name] = conversation
        return conversation


@dataclass(frozen=True)
class Actions(List[Action]):
    """
    a list of actions applied to conversations by order in which actions were applied.
    """

    def apply_action(self, action: Action, should_print: bool = True, is_color: bool = True,
                     should_append: bool = True):
        from scientistgpt.base_cast import update_cast_and_messenger_on_action
        if should_append:
            self.append(action)
        if should_print:
            print(action.pretty_repr(is_color=is_color))
            print()
        action.apply()

        # update the messenger system:
        if action.apply_to_web():
            update_cast_and_messenger_on_action(action)

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
        from .conversation_actions import ConversationAction
        return [action for action in self if
                isinstance(action, ConversationAction) and action.conversation_name == conversation_name]


@dataclass(frozen=True)
class ActionsAndConversations:
    actions: Actions = field(default_factory=Actions)
    conversations: Conversations = field(default_factory=Conversations)
