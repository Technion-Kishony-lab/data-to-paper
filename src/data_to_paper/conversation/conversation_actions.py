from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List, Set

from data_to_paper.text.highlighted_text import red_text
from data_to_paper.base_cast import Agent

from .actions_and_conversations import Action
from .message import Message
from .conversation import Conversation
from .message_designation import GeneralMessageDesignation, SingleMessageDesignation, \
    convert_general_message_designation_to_int_list
from .actions_and_conversations import Conversations

NoneType = type(None)


@dataclass(frozen=True)
class ConversationAction(Action):
    """
    Base class for actions performed on a conversation.
    """

    conversations: Conversations = None

    conversation_name: Optional[str] = None
    "The name of the conversation to perform the action on."

    driver: Optional[str] = None
    "The algorithm performing the action."

    comment: Optional[str] = None
    "A comment explaining why action is performed."

    @property
    def conversation(self) -> Conversation:
        return self.conversations.get_conversation(self.conversation_name)

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


@dataclass(frozen=True)
class ChangeConversationParticipants(ConversationAction):
    """
    Create a new conversation.
    """
    participants: Set[Agent] = None

    def _pretty_attrs(self) -> str:
        return f'name="{self.conversation_name}", ' \
               f'participants={sorted([p.name if isinstance(p, Agent) else p for p in self.participants])}'


class CreateConversation(ChangeConversationParticipants):
    """
    Create a new conversation.
    """

    def apply(self):
        if self.conversation_name is None:
            return
        self.conversations.get_or_create_conversation(
            conversation_name=self.conversation_name, participants=self.participants)


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

    message: Message = None

    delay: float = None

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

    def pretty_repr(self, is_color: bool = True, with_conversation_name: bool = True,
                    abbreviate_content: bool = False) -> str:
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
                                      is_color=is_color, abbreviate_content=abbreviate_content)
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
        self.message.index_in_conversation = len(self.conversation)
        self.message.effective_index_in_conversation = len(self.conversation.get_chosen_indices_and_messages())
        self.conversation.append(self.message)


@dataclass(frozen=True)
class BaseLLMResponse(ChangeMessagesConversationAction):
    """
    Base class for an action involving getting a response from LLM.
    """

    hidden_messages: GeneralMessageDesignation = None
    "list of message to remove from the conversation when sending to the LLM"

    def _pretty_attrs(self) -> str:
        return f'HIDING MESSAGES: {self.hidden_messages}' if self.hidden_messages else ''


@dataclass(frozen=True)
class AppendLLMResponse(AppendMessage, BaseLLMResponse):
    """
    Add a response from the LLM.
    """
    pass


@dataclass(frozen=True)
class FailedLLMResponse(BaseLLMResponse):
    """
    Failed getting a response from the LLM. Nothing is appended to the conversation.
    """

    exception: Exception = None

    def pretty_repr(self, is_color: bool = True, with_conversation_name: bool = True) -> str:
        s = f': FAILED:\n{self.exception}'
        if is_color:
            s = red_text(s)
        s = super().pretty_repr(is_color=is_color, with_conversation_name=False) + s
        return s

    def apply(self):
        pass


class NullConversationAction(ConversationAction):
    """
    Add a comment to the action list.

    The conversation is not affected by comments.
    """
    pass


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
class ReplaceLastMessage(AppendMessage):
    """
    Replace the last message with a new message.
    """
    message: Message = None

    def _pretty_attrs(self) -> str:
        return ''

    def apply(self):
        assert self.conversation[-1].role == self.message.role
        self.conversation.pop()
        super().apply()
