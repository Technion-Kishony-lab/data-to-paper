import re
from typing import List, Tuple

from .message import Message, Role
from .message_designation import GeneralMessageDesignation

# String patterns used to save and load conversations. Use unique patterns, not likely to occur in conversation.
SAVE_START = 'START>>>>> '
SAVE_END = '\n<<<<<END\n'


class Conversation(List[Message]):
    """
    Maintain a list of messages as exchanged between user and chatgpt.

    Takes care of:

    1. save/load to text.
    2. print colored-styled messages.
    """
    def append_message(self, role: Role, content: str, tag: str = '') -> Message:
        message = Message(role, content, tag)
        self.append(message)
        return message

    def append_user_message(self, content: str, tag: str = ''):
        return self.append_message(Role.USER, content, tag)

    def append_assistant_message(self, content: str, tag: str = ''):
        return self.append_message(Role.ASSISTANT, content, tag)

    def get_chosen_indices_and_messages(self, hidden_messages: GeneralMessageDesignation) -> List[Tuple[int, Message]]:
        """
        Return sub-list of messages.
        Remove commenter messages as well as all messages indicated in `hidden_messages`.
        """
        hidden_messages = hidden_messages or []
        return [(i, message) for i, message in enumerate(self)
                if i not in hidden_messages and message.role is not Role.COMMENTER]

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
