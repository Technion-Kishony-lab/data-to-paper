from typing import Dict, List, Optional


from .actions import Action, get_all_actions
from .conversation import Conversation

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
