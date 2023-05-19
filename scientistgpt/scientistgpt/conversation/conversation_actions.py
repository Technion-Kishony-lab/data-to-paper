from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional, List, Set

from scientistgpt.env import DELAY_AUTOMATIC_RESPONSES, DEBUG
from scientistgpt.utils.text_utils import red_text
from scientistgpt.base_cast import Agent

from .actions_and_conversations import Action
from .message import Message, create_message_from_other_message, Role
from .conversation import Conversation
from .message_designation import GeneralMessageDesignation, SingleMessageDesignation, \
    convert_general_message_designation_to_int_list
from .actions_and_conversations import Conversations

NoneType = type(None)


@dataclass(frozen=True)
class ConversationAction(Action):
    """
    Base class for actions performed on a chatgpt conversation.
    """

    conversations: Conversations

    conversation_name: Optional[str] = None
    "The name of the conversation to perform the action on."

    web_conversation_name: Optional[str] = None
    "The name of the web-conversation. None means do not apply the action to a web-conversation."

    driver: Optional[str] = None
    "The algorithm performing the action."

    comment: Optional[str] = None
    "A comment explaining why action is performed."

    @property
    def conversation(self) -> Conversation:
        return self.conversations.get_conversation(self.conversation_name)

    @property
    def web_conversation(self) -> Conversation:
        return self.conversations.get_conversation(self.web_conversation_name)

    def _pretty_attrs(self) -> str:
        return ''

    def pretty_repr(self, is_color: bool = True, with_conversation_name: bool = True) -> str:
        s = ''
        if self.driver:
            s += f'{self.driver}: '
        s += super().pretty_repr(is_color=is_color)
        if with_conversation_name and self.conversation_name:
            s += f' -> {self.conversation_name}'
        if self.comment:
            s += f', {self.comment}'
        if is_color:
            s = red_text(s)
        return s

    def apply_to_web(self) -> bool:
        return self.web_conversation is not None


@dataclass(frozen=True)
class SetTypingAgent(ConversationAction):
    """
    Set the typing agent.
    """
    agent: Agent = None

    def _pretty_attrs(self) -> str:
        return f'{self.agent}'


@dataclass(frozen=True)
class ChangeConversationParticipants(ConversationAction):
    """
    Create a new conversation.
    """
    participants: Set[Agent] = None

    def _pretty_attrs(self) -> str:
        return f'name={self.conversation_name} web={self.web_conversation_name}, ' \
               f'participants={[p.name if isinstance(p, Agent) else p for p in self.participants]}'

    def apply_to_web(self) -> bool:
        return False


class CreateConversation(ChangeConversationParticipants):
    """
    Create a new conversation.
    """

    def apply(self):
        if self.conversation_name is None:
            return
        self.conversations.get_or_create_conversation(
            conversation_name=self.conversation_name, participants=self.participants, is_web=False)

    def apply_to_web(self) -> bool:
        if self.web_conversation_name is None:
            return False
        if self.conversations.get_conversation(self.web_conversation_name) is not None:
            return False
        self.conversations.get_or_create_conversation(
            conversation_name=self.web_conversation_name, participants=self.participants, is_web=True)
        return True


class AddParticipantsToConversation(ChangeConversationParticipants):
    """
    Add participants to a conversation.
    """

    def apply(self):
        for participant in self.participants:
            self.conversation.add_participant(participant)


@dataclass(frozen=True)
class ChangeMessagesConversationAction(ConversationAction):
    pass


@dataclass(frozen=True)
class AppendMessage(ChangeMessagesConversationAction):
    """
    Append a message to the conversation.

    Message will be tagged with `tag`.
    If `tag` already exists, conversation will reset to the previous tag.
    """

    ROLE_TO_DELAY = {
        Role.ASSISTANT: 0,
        Role.USER: DELAY_AUTOMATIC_RESPONSES,
        Role.COMMENTER: 0,
        Role.SURROGATE: DELAY_AUTOMATIC_RESPONSES,
        Role.SYSTEM: DELAY_AUTOMATIC_RESPONSES * 0.5,
    }

    message: Message = None

    adjust_message_for_web: dict = None

    delay: float = DELAY_AUTOMATIC_RESPONSES

    parameters_for_web: dict = field(default_factory=dict)

    def _get_delay(self):
        return self.ROLE_TO_DELAY[self.message.role]

    def _get_index_of_tag(self) -> Optional[int]:
        """
        Return the index of the message with the provided tag.
        """
        if self.message.tag is None:
            return None
        try:
            return SingleMessageDesignation(self.message.tag).get_message_num(self.conversation)
        except ValueError:
            return None

    def _get_message_index(self):
        """
        Return the index of the message that will be appended to the conversation.
        """
        tag_index = self._get_index_of_tag()
        if tag_index is None:
            return len(self.conversation)
        return tag_index

    def should_add_to_conversation(self) -> bool:
        """
        Return True if the message should be added to the conversation.
        """
        return self.conversation_name is not None and not self.message.ignore

    def pretty_repr(self, is_color: bool = True, with_conversation_name: bool = True) -> str:
        # Note 1: the conversation len assumes this method is called right before the message is appended.
        # Note 2: we are only adding the text from the super method we have comments or are rewinding. Otherwise, we
        #         the message we print has the other information (conversation name and role).
        if not self.should_add_to_conversation():
            return ''
        s = ''
        if self.comment or self._pretty_attrs():
            s += super().pretty_repr(is_color=is_color, with_conversation_name=False) + '\n'
        s += self.message.pretty_repr(number=self._get_message_index() + 1,
                                      conversation_name=self.conversation_name,
                                      is_color=is_color)
        return s

    def _pretty_attrs(self) -> str:
        index = self._get_index_of_tag()
        if index is None:
            return ''
        num_deleted = len(self.conversation) - index
        return f'REWINDING {num_deleted} MESSAGES'

    def apply(self):
        """
        Append a message to the conversation.
        Reset the conversation to the previous tag if the tag already exists.
        """
        if not self.should_add_to_conversation():
            return
        message_index = self._get_message_index()
        index = self._get_index_of_tag()
        if index is not None:
            del self.conversation[index:]
        assert len(self.conversation) == message_index
        self.conversation.append(self.message)

    def get_message_for_web(self) -> Message:
        """
        Return the message that will be appended to the web conversation.
        """
        if self.adjust_message_for_web:
            return create_message_from_other_message(
                self.message,
                **self.adjust_message_for_web)
        return self.message

    def apply_to_web(self) -> bool:
        if not super().apply_to_web():
            return False
        if self.message.is_background is None and any(self.get_message_for_web() == m for m in self.web_conversation) \
                or self.message.is_background is True:
            return False
        if DEBUG and self.conversation is not None and self.should_add_to_conversation() and \
                self.message.role != Role.COMMENTER:
            self.parameters_for_web['real_index'] = len(self.conversation.get_chosen_indices_and_messages())
        else:
            self.parameters_for_web['real_index'] = None

        print('REAL INDEX = ', self.parameters_for_web['real_index'])
        if self.delay is not None:
            time.sleep(self.delay)
        self.web_conversation.append(self.get_message_for_web())
        return True


@dataclass(frozen=True)
class BaseChatgptResponse(ChangeMessagesConversationAction):
    """
    Base class for an action involving getting a response from chatgpt.
    """

    hidden_messages: GeneralMessageDesignation = None
    "list of message to remove from the conversation when sending to ChatGPT"

    def _pretty_attrs(self) -> str:
        return f'HIDING MESSAGES: {self.hidden_messages}' if self.hidden_messages else ''


@dataclass(frozen=True)
class AppendChatgptResponse(AppendMessage, BaseChatgptResponse):
    """
    Add a response from chatgpt.
    """
    pass


@dataclass(frozen=True)
class FailedChatgptResponse(BaseChatgptResponse):
    """
    Failed getting a response from chatgpt. Nothing is appended to the conversation.
    """

    exception: Exception = None

    def apply(self):
        pass


class NullConversationAction(ConversationAction):
    """
    Add a comment to the action list.

    The conversation is not affected by comments.
    """
    pass


class RegenerateLastResponse(AppendChatgptResponse):
    """
    Delete the last chatgpt response and regenerate.
    """
    def _pretty_attrs(self) -> str:
        return ' '  # not empty, to invoke printing the comment line in pretty_repr()

    def _get_index_of_tag(self) -> Optional[int]:
        return len(self.conversation) - 1


@dataclass(frozen=True)
class ResetToTag(ChangeMessagesConversationAction):
    """
    Reset the conversation back to right after the specified tag.

    By default, off_set is 0, which means the message with the specified tag will not be deleted.
    """
    tag: Optional[str] = None
    off_set: int = 0

    @property
    def _single_message_designation(self) -> SingleMessageDesignation:
        return SingleMessageDesignation(tag=self.tag, off_set=self.off_set)

    @property
    def _message_num(self) -> int:
        return self._single_message_designation.get_message_num(self.conversation)

    def _pretty_attrs(self) -> str:
        num_messages_deleted = len(self.conversation) - self._message_num - 1
        return f'{self._single_message_designation} [REWINDING {num_messages_deleted} MESSAGES]'

    def apply(self):
        del self.conversation[self._message_num + 1:]


@dataclass(frozen=True)
class DeleteMessages(ChangeMessagesConversationAction):
    """
    Delete all messages between `start` and `end`

    start/end can be int (message number), or str (message tag).
    """
    message_designation: GeneralMessageDesignation = None

    def _get_indices_to_delete(self) -> List[int]:
        """
        Return the indices of the messages to delete in reverse order (to allow consistent popping).
        """
        return convert_general_message_designation_to_int_list(self.message_designation, self.conversation)[-1::-1]

    def _pretty_attrs(self) -> str:
        return f'{self.message_designation} [{len(self._get_indices_to_delete())} MESSAGES]'

    def apply(self):
        for index in self._get_indices_to_delete():
            self.conversation.pop(index)


@dataclass(frozen=True)
class ReplaceLastResponse(AppendMessage):
    """
    Replace the last chatgpt response with a new message.
    """
    message: Message = None

    def _pretty_attrs(self) -> str:
        return ''

    def apply(self):
        self.conversation.delete_last_response()
        super().apply()


@dataclass(frozen=True)
class CopyMessagesBetweenConversations(ChangeMessagesConversationAction):
    """
    Copy messages from a source conversation to current conversation.
    """
    source_conversation_name: str = None
    message_designation: GeneralMessageDesignation = None

    @property
    def source_conversation(self) -> Conversation:
        return self.conversations.get_conversation(self.source_conversation_name)

    def _get_indices_to_copy(self) -> List[int]:
        """
        Return the indices of the messages to copy.
        """
        return convert_general_message_designation_to_int_list(self.message_designation, self.source_conversation)

    def _pretty_attrs(self) -> str:
        return f'{self.message_designation} from "{self.source_conversation_name}", ' \
               f'[{len(self._get_indices_to_copy())} MESSAGES]'

    def apply(self):
        for index in self._get_indices_to_copy():
            self.conversation.append(self.source_conversation[index])

    # TODO:  implement apply_to_web
