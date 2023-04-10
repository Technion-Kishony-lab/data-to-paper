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
