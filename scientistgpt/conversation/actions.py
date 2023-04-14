from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from scientistgpt.utils.text_utils import red_text

from .actions_and_conversations import CONVERSATION_NAMES_TO_CONVERSATIONS
from .message import Message
from .conversation import Conversation
from .message_designation import GeneralMessageDesignation, SingleMessageDesignation, \
    convert_general_message_designation_to_int_list


NoneType = type(None)


def get_name_with_new_number(conversation_name: str) -> str:
    """
    Return a new conversation name, which is not already taken, by appending a new number to the provided name.
    """
    i = 1
    while True:
        new_name = f'{conversation_name}_{i}'
        if new_name not in CONVERSATION_NAMES_TO_CONVERSATIONS:
            return new_name
        i += 1


@dataclass(frozen=True)
class Action:
    """
    Base class for actions performed on a chatgpt conversation.
    """

    conversation_name: Optional[str] = None
    "The name of the conversation to perform the action on."

    agent: Optional[str] = None
    "The agent/algorithm performing the action."

    comment: Optional[str] = None
    "A comment explaining why action is performed."

    @property
    def conversation(self) -> Conversation:
        return CONVERSATION_NAMES_TO_CONVERSATIONS[self.conversation_name]

    def default_comment(self) -> str:
        return ''

    def pretty_repr(self, is_color: bool = True) -> str:
        s = ''
        if self.agent:
            s += f'{self.agent}: '
        s += f'{type(self).__name__}'
        if self.default_comment():
            s += f'({self.default_comment()})'
        if self.conversation_name:
            s += f' -> {self.conversation_name}'
        if self.comment:
            s += f', {self.comment}'
        if is_color:
            s = red_text(s)
        return s

    def apply(self):
        pass


@dataclass(frozen=True)
class CreateConversation(Action):
    """
    Create a new conversation.
    """

    def apply(self):
        CONVERSATION_NAMES_TO_CONVERSATIONS[self.conversation_name] = \
            Conversation(conversation_name=self.conversation_name)


@dataclass(frozen=True)
class AppendMessage(Action):
    """
    Append a message to the conversation.

    Message will be tagged with `tag`.
    If `tag` already exists, conversation will reset to the previous tag.
    """
    message: Message = None

    def pretty_repr(self, is_color: bool = True) -> str:
        # Note: the conversation len assumes this method is called right after the message is appended.
        # Note: we are adding the text from the super method because the action and the message
        #       contain redundant information.
        if self.comment:
            s = self.comment
            if is_color:
                s = red_text(s)
            s += '\n'
        else:
            s = ''
        s += self.message.pretty_repr(number=len(self.conversation),
                                      conversation_name=self.conversation_name,
                                      is_color=is_color)
        return s

    def default_comment(self) -> str:
        return f'{self.message.role}'

    def apply(self):
        """
        Append a message to the conversation.
        Reset the conversation to the previous tag if the tag already exists.
        """
        if self.message.tag is not None:
            try:
                index = SingleMessageDesignation(self.message.tag).get_message_num(self.conversation)
                del self.conversation[index:]
            except ValueError:
                pass
        self.conversation.append(self.message)


@dataclass(frozen=True)
class BaseChatgptResponse(Action):
    """
    Base class for an action involving getting a response from chatgpt.
    """

    hidden_messages: GeneralMessageDesignation = None
    "list of message to remove from the conversation when sending to ChatGPT"

    def default_comment(self) -> str:
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


class NoAction(Action):
    """
    Add a comment to the action list.

    The conversation is not affected by comments.
    """
    pass


class RegenerateLastResponse(AppendChatgptResponse):
    """
    Delete the last chatgpt response and regenerate.
    """
    def default_comment(self) -> str:
        return ''

    def apply(self):
        self.conversation.delete_last_response()
        super().apply()


@dataclass(frozen=True)
class ResetToTag(Action):
    """
    Reset the conversation back to the specified tag.

    By default, off_set is 0, which means the message with the specified tag will not be deleted.
    """
    tag: Optional[str] = None
    off_set: int = 0

    def default_comment(self) -> str:
        off_set_test = '' if self.off_set == 0 else f'{self.off_set:+d}'
        return f'<{self.tag}>' + off_set_test

    def apply(self):
        index = SingleMessageDesignation(tag=self.tag, off_set=self.off_set).get_message_num(self.conversation)
        del self.conversation[index + 1:]


@dataclass(frozen=True)
class DeleteMessages(Action):
    """
    Delete all messages between `start` and `end`

    start/end can be int (message number), or str (message tag).
    """
    message_designation: GeneralMessageDesignation = None

    def default_comment(self) -> str:
        return f'{self.message_designation}'

    def apply(self):
        for index in convert_general_message_designation_to_int_list(self.message_designation,
                                                                     self.conversation)[-1::-1]:
            self.conversation.pop(index)


@dataclass(frozen=True)
class ReplaceLastResponse(AppendMessage):
    """
    Replace the last chatgpt response with a new message.
    """
    message: Message = None

    def default_comment(self) -> str:
        return ''

    def apply(self):
        self.conversation.delete_last_response()
        super().apply()


@dataclass(frozen=True)
class CopyMessagesBetweenConversations(Action):
    """
    Copy messages from a source conversation to current conversation.
    """
    source_conversation_name: str = None
    message_designation: GeneralMessageDesignation = None

    @property
    def source_conversation(self) -> Conversation:
        return CONVERSATION_NAMES_TO_CONVERSATIONS[self.source_conversation_name]

    def default_comment(self) -> str:
        return f'messages {self.message_designation} from conversation "{self.source_conversation_name}"'

    def apply(self):
        for index in convert_general_message_designation_to_int_list(self.message_designation,
                                                                     self.source_conversation):
            self.conversation.append(self.source_conversation[index])
