from _pytest.fixtures import fixture

from scientistgpt.conversation.actions import CONVERSATION_NAMES_TO_CONVERSATIONS
from scientistgpt.conversation.converation_manager import APPLIED_ACTIONS


@fixture(autouse=True)
def reset_conversations_and_actions():
    CONVERSATION_NAMES_TO_CONVERSATIONS.clear()
    APPLIED_ACTIONS.clear()
