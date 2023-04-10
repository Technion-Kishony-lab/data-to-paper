import sys
from dataclasses import dataclass
from typing import List, Optional

from .conversation import Conversation
from .message import Message, Role
from .message_designation import GeneralMessageDesignation, convert_general_message_designation_to_list
from .actions import Action, AppendMessage, DeleteMessages, ResetToTag, RegenerateLastResponse, \
    AppendChatgptResponse, FailedChatgptResponse, ReplaceLastResponse, CopyMessagesBetweenConversations, \
    CreateConversation, CONVERSATION_NAMES_TO_CONVERSATIONS
from .replay import APPLIED_ACTIONS


@dataclass
class ConversationManager:
    """
    Manages a conversation with ChatGPT.
    Maintains a complete record of actions performed on the conversation.

    Allows processing Actions that act on the conversation.
    Maintains a list of these actions.
    """

    should_print: bool = True
    """
    Indicates whether to print added actions to the console.
    """

    conversation_name: Optional[str] = None

    agent: str = ''
    """
    Name of the agent/algorithm that is instructing this conversation manager.
    """

    @property
    def conversation(self) -> Conversation:
        return CONVERSATION_NAMES_TO_CONVERSATIONS.get(self.conversation_name, None)

    def _append_and_apply_action(self, action: Action):
        """
        Apply an action to a conversation and append to the actions list.
        """
        APPLIED_ACTIONS.append(action)
        action.apply()
        if self.should_print:
            print(action.pretty_repr(), flush=True)
            print(flush=True)
            sys.stdout.flush()

    def create_conversation(self):
        self._append_and_apply_action(CreateConversation(conversation_name=self.conversation_name))

    def append_message(self, role: Role, content: str, tag: Optional[str], comment: Optional[str] = None):
        """
        Append a message to a specified conversation.
        """
        message = Message(role=role, content=content, tag=tag)
        self._append_and_apply_action(
            AppendMessage(conversation_name=self.conversation_name, agent=self.agent, comment=comment, message=message))

    def append_system_message(self, content: str, tag: Optional[str] = None, comment: Optional[str] = None):
        """
        Append a system-message to a specified conversation.
        """
        self.append_message(Role.SYSTEM, content, tag, comment)

    def append_user_message(self, content: str, tag: Optional[str] = None, comment: Optional[str] = None):
        """
        Append a user-message to a specified conversation.
        """
        self.append_message(Role.USER, content, tag, comment)

    def append_commenter_message(self, content: str, tag: Optional[str] = None, comment: Optional[str] = None):
        """
        Append a commenter-message to a specified conversation.

        Commenter messages are messages that are not sent to chatgpt,
        rather they are just used as comments to the chat.
        """
        self.append_message(Role.COMMENTER, content, tag, comment)

    def append_provided_assistant_message(self, content: str, tag: Optional[str] = None, comment: Optional[str] = None):
        """
        Append a message with a pre-determined assistant content to a conversation (as if it came from chatgpt).
        """
        self.append_message(Role.ASSISTANT, content, tag, comment)

    def get_and_append_assistant_message(self, tag: Optional[str] = None, comment: Optional[str] = None,
                                         hidden_messages: GeneralMessageDesignation = None) -> str:
        """
        Get and append a response from openai to a specified conversation.

        If failed, retry while removing more messages upstream.
        """
        hidden_messages = convert_general_message_designation_to_list(hidden_messages)
        indices_and_messages = self.conversation.get_chosen_indices_and_messages(hidden_messages)
        actual_hidden_messages = hidden_messages.copy()

        # we try to get a response. if we fail we gradually remove messages from the top,
        # starting at message 1 (message 0 is the system message).
        while True:
            content = self.try_get_and_append_chatgpt_response(tag=tag, comment=comment,
                                                               hidden_messages=actual_hidden_messages)
            if isinstance(content, str):
                return content
            if len(indices_and_messages) <= 1:
                # we tried removing all messages and failed.
                raise RuntimeError('Failed accessing openai despite removing all messages.')
            index, _ = indices_and_messages.pop(1)
            actual_hidden_messages.append(index)

    def get_actions_for_conversation(self) -> List[Action]:
        return [action for action in APPLIED_ACTIONS if action.conversation_name == self.conversation_name]

    def regenerate_previous_response(self, comment: Optional[str] = None):
        last_action = self.get_actions_for_conversation()[-1]
        assert isinstance(last_action, AppendChatgptResponse)
        # get response with the same messages removed as last time plus the last response (-1).
        content = self.conversation.try_get_chatgpt_response(last_action.hidden_messages + [-1])
        assert content is not None  # because this same query already succeeded getting response.
        self._append_and_apply_action(
            RegenerateLastResponse(
                conversation_name=self.conversation_name, agent=last_action.agent, comment=comment,
                message=Message(role=last_action.message.role,
                                content=content,
                                tag=last_action.message.tag),
                hidden_messages=last_action.hidden_messages),
        )

    def try_get_and_append_chatgpt_response(self, tag: Optional[str], comment: Optional[str] = None,
                                            hidden_messages: GeneralMessageDesignation = None) -> Optional[str]:
        """
        Try to get and append a response from openai to a specified conversation.

        The conversation is sent to openai after removing the messages with indices listed in hidden_messages.

        If getting a response is successful then append to the conversation, record action and return response string.
        If failed due to openai exception. Record a failed action and return the exception.
        """
        content = self.conversation.try_get_chatgpt_response(hidden_messages)
        if isinstance(content, Exception):
            action = FailedChatgptResponse(
                conversation_name=self.conversation_name, agent=self.agent, comment=comment,
                hidden_messages=hidden_messages,
                exception=content)
        else:
            action = AppendChatgptResponse(
                conversation_name=self.conversation_name, agent=self.agent, comment=comment,
                hidden_messages=hidden_messages,
                message=Message(role=Role.ASSISTANT,
                                content=content,
                                tag=tag))
        self._append_and_apply_action(action)
        return content

    def reset_back_to_tag(self, tag: str, comment: Optional[str] = None):
        """
        Reset the conversation to the last message with the specified tag.
        All messages following the message with the specified tag will be deleted.
        The message with the specified tag will be kept.
        """
        self._append_and_apply_action(ResetToTag(
            conversation_name=self.conversation_name, agent=self.agent, comment=comment, tag=tag))

    def delete_messages(self, message_designation: GeneralMessageDesignation, comment: Optional[str] = None):
        """
        Delete messages from a conversation.
        """
        self._append_and_apply_action(
            DeleteMessages(
                conversation_name=self.conversation_name, agent=self.agent, comment=comment,
                message_designation=message_designation))

    def replace_last_response(self, content: str, comment: Optional[str] = None, tag: Optional[str] = None):
        """
        Replace the last response with the specified content.
        """
        self._append_and_apply_action(
            ReplaceLastResponse(
                conversation_name=self.conversation_name, agent=self.agent, comment=comment,
                message=Message(role=Role.ASSISTANT, content=content, tag=tag)))

    def copy_messages_from_another_conversations(self, source_conversation: Conversation,
                                                 message_designation: GeneralMessageDesignation,
                                                 comment: Optional[str] = None):
        """
        Copy messages from one conversation to another.
        """
        self._append_and_apply_action(
            CopyMessagesBetweenConversations(
                conversation_name=self.conversation_name, agent=self.agent, comment=comment,
                source_conversation_name=source_conversation.conversation_name,
                message_designation=message_designation))
