"""
This file contains the primary list of actions and the dict of conversations.

The action list allows a formal record of all the actions that were performed on the conversations.
Using the actions, we can replay the entire conversation history.

The dict of conversations is used to keep track of conversations by name, as they are created and modified by actions.
"""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import Dict, List, TYPE_CHECKING, Union, Optional

if TYPE_CHECKING:
    from .conversation import Conversation
    from .actions import Action


CONVERSATION_NAMES_TO_CONVERSATIONS: Dict[str, Conversation] = {}
"""
a dict containing all managed conversations, by name. 
"""


APPLIED_ACTIONS: List[Action] = []
"""
a list of actions applied to conversations by order in which actions were applied.
"""


def get_conversation(conversation_name: str) -> Optional[Conversation]:
    """
    Return the conversation with the provided name.
    """
    return CONVERSATION_NAMES_TO_CONVERSATIONS.get(conversation_name, None)


def add_conversation(conversation: Conversation) -> Conversation:
    """
    Add a conversation to the dict of conversations.
    """
    CONVERSATION_NAMES_TO_CONVERSATIONS[conversation.conversation_name] = conversation
    return conversation


def get_conversation_name_with_new_number(conversation_name: str) -> str:
    """
    Return a new conversation name, which is not already taken, by appending a new number to the provided name.
    """
    i = 1
    while True:
        new_name = f'{conversation_name}_{i}'
        if new_name not in CONVERSATION_NAMES_TO_CONVERSATIONS:
            return new_name
        i += 1


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
    APPLIED_ACTIONS.clear()
    CONVERSATION_NAMES_TO_CONVERSATIONS.clear()
