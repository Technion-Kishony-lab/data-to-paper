from __future__ import annotations

from abc import abstractmethod, ABC
from dataclasses import dataclass
from typing import Union, Optional, List

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from data_to_paper import Conversation


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

    @abstractmethod
    def __str__(self):
        pass


@dataclass(frozen=True)
class SingleMessageDesignation(MessageDesignation):
    """
    Indicates a single message by its tag or position.

    tag: indicates message tag (str), or position (int).
         negative values indicates counting from the end (-1 is the last message).
    """
    tag: Union[str, int]
    off_set: int = 0

    def get_message_num(self, conversation: Conversation) -> int:
        tag = self.tag if isinstance(self.tag, int) else conversation.get_message_index_by_tag(self.tag)
        if tag < 0:
            tag = len(conversation) + tag
        return tag + self.off_set

    def get_message_nums(self, conversation: Conversation) -> List[int]:
        return [self.get_message_num(conversation)]

    def __str__(self):
        if self.off_set:
            return f"<{self.tag} {self.off_set:+d}>"
        else:
            return f"<{self.tag}>"


@dataclass(frozen=True)
class RangeMessageDesignation(MessageDesignation):
    """
    Indicates a range of messages.

    start: first message, indicated, by tag (str), by index (int) or as SingleMessageDesignation.
    end: last message (including), indicated, by tag (str), by index (int) or as SingleMessageDesignation.
    """

    start: SingleMessageDesignation
    end: SingleMessageDesignation

    def get_message_nums(self, conversation: Conversation) -> List[int]:
        return list(range(self.start.get_message_num(conversation), self.end.get_message_num(conversation) + 1))

    def __str__(self):
        return f"{self.start} - {self.end}"

    @classmethod
    def from_(cls,
              start: Optional[Union[str, int, SingleMessageDesignation]] = None,
              end: Optional[Union[str, int, SingleMessageDesignation]] = None):
        start = 0 if start is None else start
        if not isinstance(start, SingleMessageDesignation):
            start = SingleMessageDesignation(start)
        end = -1 if end is None else end
        if not isinstance(end, SingleMessageDesignation):
            end = SingleMessageDesignation(end)
        return cls(start, end)


GeneralMessageDesignation = Optional[Union[MessageDesignation, str, int, List[Union[MessageDesignation, str, int]]]]


def convert_general_message_designation_to_list(designations: GeneralMessageDesignation
                                                ) -> List[Union[MessageDesignation, str, int]]:
    if designations is None:
        return []
    if isinstance(designations, list):
        return designations
    if isinstance(designations, tuple):
        return list(designations)
    return [designations]


def convert_general_message_designation_to_int_list(designations: GeneralMessageDesignation,
                                                    conversation: Conversation) -> List[int]:
    indices = set()
    for designation in convert_general_message_designation_to_list(designations):
        if isinstance(designation, tuple):
            designation = RangeMessageDesignation.from_(*designation)
        elif not isinstance(designation, MessageDesignation):
            designation = SingleMessageDesignation(designation)
        indices |= set(designation.get_message_nums(conversation))
    indices = sorted(indices)
    return indices
