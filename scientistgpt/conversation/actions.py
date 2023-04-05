from dataclasses import dataclass
from typing import Union, Optional, List

from scientistgpt.utils.text_utils import print_red
from .message import Message
from .conversation import Conversation
from .message_designation import MessageDesignation, SingleMessageDesignation, RangeMessageDesignation

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

    def display(self, conversation_name: Optional[str]):
        if self.agent:
            print_red(f'{self.agent}: ', end='')
        print_red(f'{type(self)}->{conversation_name}. {self.default_comment()} {self.comment}')

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
    
    def display(self, conversation_name: Optional[str]):
        super().display(conversation_name)
        self.message.display()

    def apply(self, conversation: Conversation):
        conversation.append(self.message)


@dataclass(frozen=True)
class BaseChatgptResponse(Action):
    """
    Base class for an action of getting a response from chatgpt.
    """

    removed_messages: List[MessageDesignation] = None
    "list of message indices to remove when approaching chatGPT"

    def default_comment(self) -> str:
        return f'Message {self.removed_messages} were hidden. ' if self.removed_messages else ''


class AddChatgptResponse(AppendMessage, BaseChatgptResponse):
    """
    Get a response from chatgpt and append to the conversation.
    """
    pass


@dataclass(frozen=True)
class FailedChatgptResponse(BaseChatgptResponse):
    """
    Failed getting a response from chatgpt. Nothing is appended to the conversation.
    """

    exception: Exception = None

    def default_comment(self) -> str:
        return super().default_comment() + ' Failed getting ChatGPT response.'

    def apply(self, conversation: Conversation):
        pass


class AddComment(Action):
    """
    Add a comment to the action list.

    The conversation is not affected by comments.
    """
    pass


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


class RegenerateLastResponse(AddChatgptResponse):
    """
    Delete the last chatgpt response and regenerate.
    """
    def default_comment(self) -> str:
        return 'Regenerating chatgpt response.'

    def apply(self, conversation: Conversation):
        conversation.delete_last_response()
        super().apply(conversation)


@dataclass(frozen=True)
class DeleteMessages(Action):
    """
    Delete all messages between `start` and `end`

    start/end can be int (message number), or str (message tag).
    """
    start: Optional[Union[str, int, SingleMessageDesignation]] = None
    end: Optional[Union[str, int, SingleMessageDesignation]] = None

    def default_comment(self) -> str:
        return f'Deleting all messages from {self.start} to {self.end}.'

    def apply(self, conversation: Conversation):
        for index in RangeMessageDesignation(start=self.start, end=self.end).get_message_num(conversation):
            del conversation[index: index + 1]
