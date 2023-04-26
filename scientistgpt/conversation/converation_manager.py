from dataclasses import dataclass
from typing import Optional, Set, Iterable

from scientistgpt.cast import Agent

from .actions_and_conversations import get_actions_for_conversation, get_conversation
from .conversation import Conversation
from .message import Message, Role, create_message, create_message_from_other_message
from .message_designation import GeneralMessageDesignation, convert_general_message_designation_to_list
from .actions import Action, AppendMessage, DeleteMessages, ResetToTag, RegenerateLastResponse, \
    AppendChatgptResponse, FailedChatgptResponse, ReplaceLastResponse, CopyMessagesBetweenConversations, \
    CreateConversation, apply_action, AddParticipantsToConversation
from ..run_gpt_code.code_runner import add_python_to_first_triple_quotes_if_missing


@dataclass
class ConversationManager:
    """
    Manages a conversation with ChatGPT.
    Maintains a complete record of actions performed on the conversation.

    Allows processing Actions that act on the conversation.
    Maintains a list of these actions.
    """

    should_print: bool = True
    "Indicates whether to print added actions to the console."

    conversation_name: Optional[str] = None

    driver: str = ''
    "Name of the algorithm that is instructing this conversation manager."

    assistant_agent: Agent = None
    "The agent who is playing the assistant in the conversation."

    user_agent: Agent = None
    "The agent who is playing the user in the conversation."

    @property
    def conversation(self) -> Conversation:
        return get_conversation(self.conversation_name)

    @property
    def participants(self) -> Set[Agent]:
        return {self.assistant_agent, self.user_agent}

    def _append_and_apply_action(self, action: Action):
        """
        Apply an action to a conversation and append to the actions list.
        """
        apply_action(action, should_print=self.should_print, is_color=True)

    def create_conversation(self):
        self._append_and_apply_action(CreateConversation(conversation_name=self.conversation_name,
                                                         driver=self.driver,
                                                         participants=self.participants))

    def add_participants(self, agents: Iterable[Agent]):
        self._append_and_apply_action(AddParticipantsToConversation(conversation_name=self.conversation_name,
                                                                    driver=self.driver,
                                                                    participants=set(agents)))

    def initialize_conversation_if_needed(self):
        if self.conversation is None:
            self.create_conversation()
        else:
            if self.participants - self.conversation.participants:
                self.add_participants(self.participants - self.conversation.participants)

<<<<<<<
    def append_message(self, role: Role, content: str, tag: Optional[str], comment: Optional[str] = None,
                       ignore: bool = False, previous_code: Optional[str] = None):
=======
    def append_message(self, message: Message, comment: Optional[str] = None):
>>>>>>>
        """
        Append a message to a specified conversation.
        """
        self._append_and_apply_action(AppendMessage(
            conversation_name=self.conversation_name, driver=self.driver, comment=comment, message=message))

    def create_and_append_message(self, role: Role, content: str, tag: Optional[str], comment: Optional[str] = None,
                                  ignore: bool = False, is_code: bool = False, previous_code: Optional[str] = None):
        """
        Append a message to a specified conversation.
        """
        if role in [Role.ASSISTANT, Role.SURROGATE, Role.SYSTEM]:
            agent = self.assistant_agent
        elif role == Role.USER:
            agent = self.user_agent
        else:
            agent = None
        message = create_message(role=role, content=content, tag=tag, agent=agent, ignore=ignore,
<<<<<<<
                                 previous_code=previous_code)
        self._append_and_apply_action(AppendMessage(
            conversation_name=self.conversation_name, driver=self.driver, comment=comment, message=message))
=======
                                 is_code=is_code, previous_code=previous_code)
        self.append_message(message, comment)
>>>>>>>

    def append_system_message(self, content: str, tag: Optional[str] = None, comment: Optional[str] = None):
        """
        Append a system-message to a specified conversation.
        """
        tag = tag or 'system_prompt'
        self.create_and_append_message(Role.SYSTEM, content, tag, comment)

    def append_user_message(self, content: str, tag: Optional[str] = None, comment: Optional[str] = None,
                            ignore: bool = False, previous_code: Optional[str] = None):
        """
        Append a user-message to a specified conversation.
        """
<<<<<<<
        self.append_message(Role.USER, content, tag, comment, ignore, previous_code)
=======
        self.create_and_append_message(Role.USER, content, tag, comment, is_code, ignore, previous_code)
>>>>>>>

    def append_commenter_message(self, content: str, tag: Optional[str] = None, comment: Optional[str] = None):
        """
        Append a commenter-message to a specified conversation.

        Commenter messages are messages that are not sent to chatgpt,
        rather they are just used as comments to the chat.
        """
        self.create_and_append_message(Role.COMMENTER, content, tag, comment)

    def append_surrogate_message(self, content: str, tag: Optional[str] = None, comment: Optional[str] = None,
                                 ignore: bool = False, previous_code: Optional[str] = None):
        """
        Append a message with a pre-determined assistant content to a conversation (as if it came from chatgpt).
        """
<<<<<<<
        self.append_message(Role.SURROGATE, content, tag, comment, ignore, previous_code)
=======
        self.create_and_append_message(Role.SURROGATE, content, tag, comment, ignore, is_code, previous_code)
>>>>>>>

    def get_and_append_assistant_message(self, tag: Optional[str] = None, comment: Optional[str] = None,
                                         is_code: bool = False, previous_code: Optional[str] = None,
                                         hidden_messages: GeneralMessageDesignation = None, **kwargs) -> str:
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
                                                               is_code=is_code, previous_code=previous_code,
                                                               hidden_messages=actual_hidden_messages,
                                                               **kwargs)
            if isinstance(content, str):
                return content
            if len(indices_and_messages) <= 1:
                # we tried removing all messages and failed.
                raise RuntimeError('Failed accessing openai despite removing all messages.')
            index, _ = indices_and_messages.pop(1)
            actual_hidden_messages.append(index)

    def regenerate_previous_response(self, comment: Optional[str] = None) -> str:
        last_action = get_actions_for_conversation(self.conversation_name)[-1]
        assert isinstance(last_action, AppendChatgptResponse)
        # get response with the same messages removed as last time plus the last response (-1).
        content = self.conversation.try_get_chatgpt_response(last_action.hidden_messages + [-1])
        assert content is not None  # because this same query already succeeded getting response.
        self._append_and_apply_action(
            RegenerateLastResponse(
                conversation_name=self.conversation_name, driver=last_action.driver, comment=comment,
                message=create_message_from_other_message(last_action.message, content=content),
                hidden_messages=last_action.hidden_messages),
        )
        return content

    def try_get_and_append_chatgpt_response(self, tag: Optional[str], comment: Optional[str] = None,
                                            is_code: bool = False, previous_code: Optional[str] = None,
                                            hidden_messages: GeneralMessageDesignation = None, **kwargs
                                            ) -> Optional[str]:
        """
        Try to get and append a response from openai to a specified conversation.

        The conversation is sent to openai after removing the messages with indices listed in hidden_messages.

        If getting a response is successful then append to the conversation, record action and return response string.
        If failed due to openai exception. Record a failed action and return the exception.
        """
        content = self.conversation.try_get_chatgpt_response(hidden_messages, **kwargs)
        if isinstance(content, Exception):
            action = FailedChatgptResponse(
                conversation_name=self.conversation_name, driver=self.driver, comment=comment,
                hidden_messages=hidden_messages,
                exception=content)
        else:
            if is_code:
                content = add_python_to_first_triple_quotes_if_missing(content)
            action = AppendChatgptResponse(
                conversation_name=self.conversation_name, driver=self.driver, comment=comment,
                hidden_messages=hidden_messages,
                message=create_message(role=Role.ASSISTANT, content=content, tag=tag, agent=self.assistant_agent,
                                       previous_code=previous_code))
        self._append_and_apply_action(action)
        return content

    def reset_back_to_tag(self, tag: str, comment: Optional[str] = None):
        """
        Reset the conversation to the last message with the specified tag.
        All messages following the message with the specified tag will be deleted.
        The message with the specified tag will be kept.
        """
        self._append_and_apply_action(ResetToTag(
            conversation_name=self.conversation_name, driver=self.driver, comment=comment, tag=tag))

    def delete_messages(self, message_designation: GeneralMessageDesignation, comment: Optional[str] = None):
        """
        Delete messages from a conversation.
        """
        self._append_and_apply_action(
            DeleteMessages(
                conversation_name=self.conversation_name, driver=self.driver, comment=comment,
                message_designation=message_designation))

    def replace_last_response(self, content: str, comment: Optional[str] = None, tag: Optional[str] = None):
        """
        Replace the last response with the specified content.
        """
        self._append_and_apply_action(
            ReplaceLastResponse(
                conversation_name=self.conversation_name, driver=self.driver, comment=comment,
                message=Message(role=Role.SURROGATE, content=content, tag=tag)))
        return content

    def copy_messages_from_another_conversations(self, source_conversation: Conversation,
                                                 message_designation: GeneralMessageDesignation,
                                                 comment: Optional[str] = None):
        """
        Copy messages from one conversation to another.
        """
        self._append_and_apply_action(
            CopyMessagesBetweenConversations(
                conversation_name=self.conversation_name, driver=self.driver, comment=comment,
                source_conversation_name=source_conversation.conversation_name,
                message_designation=message_designation))
