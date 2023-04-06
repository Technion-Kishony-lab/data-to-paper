from abc import ABC
from dataclasses import dataclass
from typing import Union, Optional, List

from scientistgpt.utils.text_utils import print_red, red_text
from .message import Message
from .conversation import Conversation
from .message_designation import GeneralMessageDesignation, SingleMessageDesignation, RangeMessageDesignation, \
    convert_general_message_designation_to_int_list

NoneType = type(None)


@dataclass(frozen=True)
class Action:
    """
    Base class for actions performed on a chatgpt conversation.
    """

    agent: Optional[str] = None
    "The agent/algorithm performing the action."

    comment: Optional[str] = None
    "A comment explaining why action is performed."

    def default_comment(self) -> str:
        return ''

    def pretty_repr(self, conversation_name: Optional[str], is_color: bool = True) -> str:
        s = ''
        if self.agent:
            s += f'{self.agent}: '
        s += f'{type(self).__name__}'
        if conversation_name:
            s += f' -> {conversation_name}'
        if self.default_comment():
            s += f', {self.default_comment()}'
        if self.comment:
            s += f', {self.comment}'
        if is_color:
            s = red_text(s)
        return s

    def apply(self, conversation: Conversation):
        pass


@dataclass(frozen=True)
class AppendMessage(Action):
    """
    Append a message to the conversation.

    Message will be tagged with `tag`.
    If `tag` already exists, conversation will reset to the previous tag.
    """
    message: Message = None
    
    def pretty_repr(self, conversation_name: Optional[str], is_color: bool = True) -> str:
        return super().pretty_repr(conversation_name, is_color) + '\n' + self.message.pretty_repr(is_color=is_color)

    def apply(self, conversation: Conversation):
        conversation.append(self.message)


@dataclass(frozen=True)
class BaseChatgptResponse(Action):
    """
    Base class for an action of getting a response from chatgpt.
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

    def default_comment(self) -> str:
        return super().default_comment() + ', CHATGPT FAILED'

    def apply(self, conversation: Conversation):
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
        return 'Regenerating chatgpt response.'

    def apply(self, conversation: Conversation):
        conversation.delete_last_response()
        super().apply(conversation)


@dataclass(frozen=True)
class ResetToTag(Action):
    """
    Reset the conversation back to the specified tag.
    """
    tag: Optional[str] = None
    off_set: int = 0

    def default_comment(self) -> str:
        off_set_test = '' if self.off_set == 0 else f'{self.off_set:+d}'
        return f'Resetting conversation to tag <{self.tag}>' + off_set_test

    def apply(self, conversation: Conversation):
        index = SingleMessageDesignation(tag=self.tag, off_set=self.off_set).get_message_num(conversation)
        del conversation[index:]


@dataclass(frozen=True)
class DeleteMessages(Action):
    """
    Delete all messages between `start` and `end`

    start/end can be int (message number), or str (message tag).
    """
    message_designation: GeneralMessageDesignation = None

    def default_comment(self) -> str:
        return f'Deleting messages: {self.message_designation}.'

    def apply(self, conversation: Conversation):
        for index in convert_general_message_designation_to_int_list(self.message_designation, conversation)[-1::-1]:
            conversation.pop(index)
