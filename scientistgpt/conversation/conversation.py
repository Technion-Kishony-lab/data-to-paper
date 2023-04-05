import re
from typing import List, Tuple

from .message import Message, Role


# Use unique patterns, not likely to occur in conversation:
SAVE_START = 'START>>>>> '
SAVE_END = '\n<<<<<END\n'


class Conversation(List[Message]):
    """
    Maintain a list of messages as exchanged between user and chatgpt.

    Takes care of:

    1. save/load to text.
    2. print colored-styled messages.
    """

    def get_chosen_indices_and_messages(self, removed_messages: list[int] = None) -> List[Tuple[int, Message]]:
        """
        Return sub-list of messages.
        Remove messages indicated in `removed_messages` as well as commenter messages.
        """
        removed_messages = removed_messages or []
        return [(i, message) for i, message in enumerate(self)
                if i not in removed_messages and message.role is not Role.COMMENTER]

    def get_last_response(self):
        assert self[-1].role is Role.ASSISTANT
        return self[-1].content

    def delete_last_response(self):
        assert self[-1].role is Role.ASSISTANT
        self.pop()

    def save(self, filename: str):
        with open(filename, 'w') as f:
            for message in self:
                f.write(f'{SAVE_START}{message.convert_to_text()}{SAVE_END}\n\n')

    def load(self, filename: str):
        self.clear()
        with open(filename, 'r') as f:
            entire_file = f.read()
            matches = re.findall(SAVE_START + "(.*?)" + SAVE_END, entire_file, re.DOTALL)
            for match in matches:
                self.append(Message.from_text(match))

    @classmethod
    def from_file(cls, filename: str):
        self = cls()
        self.load(filename)
        return self

    def print_all_messages(self):
        for message in self:
            message.display()
