from typing import Dict, List, Optional, Set

from .actions import Action, get_all_actions
from .conversation import Conversation, WebConversation
from scientistgpt.base_cast import Agent

CONVERSATION_NAMES_TO_CONVERSATIONS: Dict[str, Conversation] = {}
"""
a dict containing all managed conversations, by name. 
"""


def get_actions_for_conversation(conversation_name: str) -> List[Action]:
    """
    Return a list of actions that were applied to the conversation with the provided name.
    """
    from .conversation_actions import ConversationAction
    return [action for action in get_all_actions() if
            isinstance(action, ConversationAction) and action.conversation_name == conversation_name]


def get_conversation(conversation_name: str) -> Optional[Conversation]:
    """
    Return the conversation with the provided name.
    """
    return CONVERSATION_NAMES_TO_CONVERSATIONS.get(conversation_name, None)


def get_or_create_conversation(conversation_name: str, participants: Set[Agent] = None, is_web: bool = False
                               ) -> Conversation:
    if conversation_name in CONVERSATION_NAMES_TO_CONVERSATIONS:
        return CONVERSATION_NAMES_TO_CONVERSATIONS[conversation_name]
    conversation = Conversation(conversation_name=conversation_name, participants=participants) if not is_web \
        else WebConversation(conversation_name=conversation_name, participants=participants)
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
