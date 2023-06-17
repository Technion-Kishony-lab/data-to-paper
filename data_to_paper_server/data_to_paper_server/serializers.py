from dataclasses import dataclass
from typing import Optional

from data_to_paper.conversation.actions_and_conversations import Action
from data_to_paper.conversation.conversation import WEB_CONVERSATION_NAME_PREFIX
from data_to_paper.conversation.conversation_actions import CreateConversation, AppendMessage, SetTypingAgent
from data_to_paper.conversation.stage import AdvanceStage, SetActiveConversation, SetProduct
from data_to_paper.env import SHOW_CHATGPT_CONTEXT


@dataclass
class SerializedAction:
    event: str
    data: dict


def remove_conversation_name_prefix(conversation_name: str) -> str:
    """
    Remove the prefix from a conversation name.
    """
    return conversation_name[len(WEB_CONVERSATION_NAME_PREFIX):]


def serialize_action(action: Action) -> Optional[SerializedAction]:
    """
    Serialize an action to a dict.
    """
    if isinstance(action, AppendMessage):
        message = action.get_message_for_web()
        agent = message.agent
        content = message.pretty_content(text_color='', width=90, is_html=True, with_header=SHOW_CHATGPT_CONTEXT.val)
        return SerializedAction('AppendMessage', {
            'conversationName': remove_conversation_name_prefix(action.web_conversation_name),
            'message': content,
            'sender': agent.value if agent else None,
            'senderCast': agent.profile.name if agent else None,
            'role': message.role.value,
        })
    if isinstance(action, CreateConversation):
        other = [agent for agent in action.participants if agent != agent.get_primary_agent()][0]
        return SerializedAction('CreateConversation', {
            'contact': other.value,
            'contactPretty': other.pretty_name(),
            'conversationName': remove_conversation_name_prefix(action.web_conversation_name),
        })
    if isinstance(action, AdvanceStage):
        return SerializedAction('AdvanceStage', {
            'stage': action.stage,
        })
    if isinstance(action, SetActiveConversation):
        return SerializedAction('SetActiveConversation', {
            'conversationName': action.conversation_name,
            'contact': action.agent.pretty_name(),
        })
    if isinstance(action, SetProduct):
        return SerializedAction('SetProduct', {
            'productDescription': action.get_product_description(),
            'stage': action.stage,
        })
    if isinstance(action, SetTypingAgent):
        return SerializedAction('SetTypingAgent', {
            'conversationName': remove_conversation_name_prefix(action.web_conversation_name),
            'typingAgent': action.agent.profile.name,
        })
    return None
