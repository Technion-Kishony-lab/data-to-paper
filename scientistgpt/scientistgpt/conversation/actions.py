"""
This file contains the primary list of actions and the dict of conversations.

The action list allows a formal record of all the actions that were performed on the conversations.
Using the actions, we can replay the entire conversation history.

The dict of conversations is used to keep track of conversations by name, as they are created and modified by actions.
"""

from __future__ import annotations

import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import List, Union


def apply_action(action: Action, should_print: bool = True, is_color: bool = True):
    from scientistgpt.base_cast import update_cast_and_messenger_on_action
    append_action(action)
    if should_print:
        print(action.pretty_repr(is_color=is_color))
        print()
    action.apply()

    # update the messenger system:
    if action.apply_to_web():
        update_cast_and_messenger_on_action(action)


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


APPLIED_ACTIONS: List[Action] = []
"""
a list of actions applied to conversations by order in which actions were applied.
"""


def get_all_actions() -> List[Action]:
    """
    Get the primary list of actions.
    """
    return APPLIED_ACTIONS


def append_action(action: Action):
    """
    Append an action to the primary list of actions.
    """
    APPLIED_ACTIONS.append(action)


def save_actions_to_file(file_path: Union[str, Path]):
    """
    Save the primary list of actions to a json file.
    """
    with open(file_path, 'wb') as f:
        pickle.dump(APPLIED_ACTIONS, f)


def load_actions_from_file(file_path: Union[str, Path]) -> List[Action]:
    """
    Load a list of actions from a json file.
    """
    with open(file_path, 'rb') as f:
        return pickle.load(f)


def clear_actions_and_conversations():
    """
    Clear the primary list of actions.
    """
    from .store_conversations import CONVERSATION_NAMES_TO_CONVERSATIONS
    APPLIED_ACTIONS.clear()
    CONVERSATION_NAMES_TO_CONVERSATIONS.clear()
