import contextlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, NamedTuple

from .conversation import Conversation
from .message import Message, Role
from .message_designation import GeneralMessageDesignation, convert_general_message_designation_to_list
from .actions import Action, AppendMessage, DeleteMessages, ResetToTag, RegenerateLastResponse, \
    AppendChatgptResponse, FailedChatgptResponse, ReplaceLastResponse, CopyMessagesBetweenConversations


class ConversationNameAndAction(NamedTuple):
    name: str
    action: Action


@dataclass
class ConversationManager:
    """
    Manages multiple conversations with ChatGPT.
    Maintains a complete record of actions performed on these conversations.

    Allows processing Actions that act on the conversation.
    Maintains a list of these actions.
    """

    conversations: Dict[Optional[str], Conversation] = field(default_factory=dict)
    """
    a dict containing the managed conversations. The key is typically a string, 
    but can also be `None` for the main/default conversation.
    """

    conversation_names_and_actions: List[ConversationNameAndAction] = field(default_factory=list)
    """
    a list of actions, and the conversations to which they were applied, 
    by order in which actions were applied.
    """

    should_print: bool = True
    """
    Indicates whether to print added actions to the console.
    """

    conversation_name: Optional[str] = None

    @contextlib.contextmanager
    def temporary_set_conversation_name(self, conversation_name: Optional[str]):
        """
        Set the conversation name for the duration of the context.
        """
        old_conversation_name = self.conversation_name
        self.conversation_name = conversation_name
        yield
        self.conversation_name = old_conversation_name

    def create_conversation(self) -> Conversation:
        new_conversation = Conversation()
        self.conversations[self.conversation_name] = new_conversation
        return new_conversation

    def get_conversation(self) -> Conversation:
        return self.conversations[self.conversation_name]

    def _append_and_apply_action(self, action: Action):
        """
        Apply an action to a conversation and append to the actions list.
        """
        self.conversation_names_and_actions.append(ConversationNameAndAction(self.conversation_name, action))
        action.apply(self.get_conversation(), self)
        if self.should_print:
            print(action.pretty_repr(self.conversation_name))

    def append_message(self, role: Role, content: str, tag: Optional[str],
                       agent: Optional[str] = None,
                       comment: Optional[str] = None):
        """
        Append a message to a specified conversation.
        """
        message = Message(role=role, content=content, tag=tag)
        self._append_and_apply_action(action=AppendMessage(agent=agent, comment=comment, message=message))

    def append_system_message(self, content: str, tag: Optional[str] = None,
                              agent: Optional[str] = None,
                              comment: Optional[str] = None):
        """
        Append a system-message to a specified conversation.
        """
        self.append_message(Role.SYSTEM, content, tag, agent, comment)

    def append_user_message(self, content: str, tag: Optional[str] = None,
                            agent: Optional[str] = None,
                            comment: Optional[str] = None):
        """
        Append a user-message to a specified conversation.
        """
        self.append_message(Role.USER, content, tag, agent, comment)

    def append_commenter_message(self, content: str, tag: Optional[str] = None,
                                 agent: Optional[str] = None,
                                 comment: Optional[str] = None):
        """
        Append a commenter-message to a specified conversation.

        Commenter messages are messages that are not sent to chatgpt,
        rather they are just used as comments to the chat.
        """
        self.append_message(Role.COMMENTER, content, tag, agent, comment)

    def append_provided_assistant_message(self, content: str, tag: Optional[str] = None,
                                          agent: Optional[str] = None,
                                          comment: Optional[str] = None):
        """
        Append a message with a pre-determined assistant content to a conversation (as if it came from chatgpt).
        """
        self.append_message(Role.ASSISTANT, content, tag, agent, comment)

    def get_and_append_assistant_message(self, tag: Optional[str] = None,
                                         agent: Optional[str] = None,
                                         comment: Optional[str] = None,
                                         hidden_messages: GeneralMessageDesignation = None) -> str:
        """
        Get and append a response from openai to a specified conversation.

        If failed, retry while removing more messages upstream.
        """
        hidden_messages = convert_general_message_designation_to_list(hidden_messages)
        indices_and_messages = self.get_conversation().get_chosen_indices_and_messages(hidden_messages)
        actual_hidden_messages = hidden_messages.copy()

        # we try to get a response. if we fail we gradually remove messages from the top,
        # starting at message 1 (message 0 is the system message).
        for index, _ in indices_and_messages[1:]:
            content = self.try_get_and_append_chatgpt_response(tag=tag, agent=agent,
                                                               comment=comment, hidden_messages=actual_hidden_messages)
            if isinstance(content, str):
                return content
            actual_hidden_messages.append(index)
        raise RuntimeError('Failed accessing openai despite removing all messages.')

    def get_actions_for_conversation(self) -> List[Action]:
        return [action for name, action in self.conversation_names_and_actions if name == self.conversation_name]

    def regenerate_previous_response(self):
        last_action = self.get_actions_for_conversation()[-1]
        assert isinstance(last_action, AppendChatgptResponse)
        # get response with the same messages removed as last time plus the last response (-1).
        content = self.get_conversation().try_get_chatgpt_response(last_action.hidden_messages + [-1])
        assert content is not None  # because this same query already succeeded getting response.
        self._append_and_apply_action(
            RegenerateLastResponse(agent=last_action.agent,
                                   comment=last_action.comment,
                                   message=Message(role=last_action.message.role,
                                                   content=content,
                                                   tag=last_action.message.tag),
                                   hidden_messages=last_action.hidden_messages),
        )

    def try_get_and_append_chatgpt_response(self, tag: Optional[str],
                                            agent: Optional[str] = None,
                                            comment: Optional[str] = None,
                                            hidden_messages: GeneralMessageDesignation = None) -> Optional[str]:
        """
        Try to get and append a response from openai to a specified conversation.

        The conversation is sent to openai after removing the messages with indices listed in hidden_messages.

        If getting a response is successful then append to the conversation, record action and return response string.
        If failed due to openai exception. Record a failed action and return the exception.
        """
        content = self.get_conversation().try_get_chatgpt_response(hidden_messages)
        if isinstance(content, Exception):
            action = FailedChatgptResponse(agent=agent, comment=comment, hidden_messages=hidden_messages,
                                           exception=content)
        else:
            action = AppendChatgptResponse(agent=agent, comment=comment,
                                           hidden_messages=hidden_messages,
                                           message=Message(role=Role.ASSISTANT,
                                                           content=content,
                                                           tag=tag))
        self._append_and_apply_action(action)
        return content

    def reset_back_to_tag(self, tag: str,
                          agent: Optional[str] = None,
                          comment: Optional[str] = None,
                          ):
        """
        Reset the conversation to the last message with the specified tag.
        """
        self._append_and_apply_action(ResetToTag(agent=agent, comment=comment, tag=tag))

    def delete_messages(self, message_designation: GeneralMessageDesignation,
                        agent: Optional[str] = None,
                        comment: Optional[str] = None,
                        ):
        """
        Delete messages from a conversation.
        """
        self._append_and_apply_action(
            DeleteMessages(agent=agent, comment=comment, message_designation=message_designation))

    def replace_last_response(self, content: str,
                              agent: Optional[str] = None,
                              comment: Optional[str] = None,
                              tag: Optional[str] = None,
                              ):
        """
        Replace the last response with the specified content.
        """
        self._append_and_apply_action(
            ReplaceLastResponse(agent=agent, comment=comment,
                                message=Message(role=Role.ASSISTANT, content=content, tag=tag)))

    def copy_messages_from_another_conversations(self, source_conversation_name: str,
                                                 message_designation: GeneralMessageDesignation,
                                                 agent: Optional[str] = None,
                                                 comment: Optional[str] = None,
                                                 ):
        """
        Copy messages from one conversation to another.
        """
        self._append_and_apply_action(
            CopyMessagesBetweenConversations(agent=agent, comment=comment,
                                             source_conversation_name=source_conversation_name,
                                             message_designation=message_designation))