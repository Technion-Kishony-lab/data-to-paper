from abc import abstractmethod, ABC
from dataclasses import dataclass
from typing import NamedTuple, Union, Optional, List

from scientistgpt import Conversation


@dataclass(frozen=True)
class MessageDesignation(ABC):
    """
    a base class for indicating specific messages, or range of messages, within a conversation.
    """

    @abstractmethod
    def get_message_nums(self, conversation) -> List[int]:
        """
        Returns a list of indices indicating chosen messages in `conversation`.
        """
        pass


@dataclass(frozen=True)
class SingleMessageDesignation(MessageDesignation):
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


@dataclass(frozen=True)
class RangeMessageDesignation(MessageDesignation):
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


GeneralMessageDesignation = Optional[Union[MessageDesignation, str, int, List[MessageDesignation, str, int]]]


def convert_general_message_designation_to_list(designations: GeneralMessageDesignation
                                                ) -> List[Union[MessageDesignation, str, int]]:
    if designations is None:
        return []
    if isinstance(designations, list):
        return designations
    return [designations]


def convert_general_message_designation_to_int_list(designations: GeneralMessageDesignation,
                                                    conversation: Conversation) -> List[int]:
    indices = set()
    for designation in convert_general_message_designation_to_list(designations):
        if not isinstance(designation, MessageDesignation):
            designation = SingleMessageDesignation(designation)
        indices |= designation.get_message_nums(conversation)
    indices = list(indices)
    indices.sort()
    return indices
