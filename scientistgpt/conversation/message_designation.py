from abc import abstractmethod, ABC
from typing import NamedTuple, Union, Optional, List

from scientistgpt import Conversation


class MessageDesignation(NamedTuple, ABC):
    """
    a base class for indicating specific messages, or range of messages, within a conversation.
    """

    @abstractmethod
    def get_message_nums(self, conversation) -> List[int]:
        """
        Returns a list of indices indicating chosen messages in `conversation`.
        """
        pass


class SingleMessageDesignation(NamedTuple, MessageDesignation):
    """
    Indicates a single message by its tag or position.

    tag: indicates message tag (str), or position (int).
    """
    tag: Union[str, int]
    off_set: int = 0

    def get_message_num(self, conversation: Conversation) -> int:
        tag = self.tag if isinstance(self.tag, int) else [message.tag for message in conversation].index(self.tag)
        return tag + self.off_set

    def get_message_nums(self, conversation: Conversation) -> List[int]:
        return [self.get_message_num(conversation)]


class RangeMessageDesignation(NamedTuple, MessageDesignation):
    """
    Indicates a range of messages.

    start: first message, indicated, by tag (str), by index (int) or as SingleMessageDesignation.
    end: last message (not including), indicated, by tag (str), by index (int) or as SingleMessageDesignation.
    """
    start: Optional[Union[str, int, SingleMessageDesignation]] = None
    end: Optional[Union[str, int, SingleMessageDesignation]] = None

    def get_message_nums(self, conversation: Conversation) -> List[int]:
        start = 0 if self.start is None else self.start
        if not isinstance(start, SingleMessageDesignation):
            start = SingleMessageDesignation(start)
        end = len(conversation) if self.end is None else self.end
        if not isinstance(end, SingleMessageDesignation):
            end = SingleMessageDesignation(end)
        return list(range(start.get_message_nums(conversation)[0], end.get_message_nums(conversation)[0]))


class MultiRangeMessageDesignation(NamedTuple, MessageDesignation):
    """
    Indicates a union of ranges of messages.
    """
    designations: List[RangeMessageDesignation, SingleMessageDesignation]
    
    def get_message_nums(self, conversation) -> List[int]:
        chosen = []
        for designation in self.designations:
            chosen.extend(designation.get_message_nums(conversation))
        return chosen
