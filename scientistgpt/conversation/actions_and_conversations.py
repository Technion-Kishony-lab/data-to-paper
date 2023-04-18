"""
This file contains the primary list of actions and the dict of conversations.

The action list allows a formal record of all the actions that were performed on the conversations.
Using the actions, we can replay the entire conversation history.

The dict of conversations is used to keep track of conversations by name, as they are created and modified by actions.
"""

from __future__ import annotations
from typing import Dict, List, TYPE_CHECKING

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


def get_name_with_new_number(conversation_name: str) -> str:
    """
    Return a new conversation name, which is not already taken, by appending a new number to the provided name.
    """
    i = 1
    while True:
        new_name = f'{conversation_name}_{i}'
        if new_name not in CONVERSATION_NAMES_TO_CONVERSATIONS:
            return new_name
        i += 1
