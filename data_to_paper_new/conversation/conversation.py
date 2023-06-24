from dataclasses import dataclass, field

from data_to_paper_new.conversation.message import Message
from data_to_paper_new.roles.base_role import Role


@dataclass
class Conversation:
    """
    A class that represent a conversation between chatgpt and the client
    contains all messages between them regarding the paper
    """
    conversation_name: str
    conversation_role: Role
    _messages_list: list[Message] = field(default_factory=list)


    def __init__(self, conversation_name: str, conversation_role: Role):
        self.conversation_name = conversation_name
        self.conversation_role = conversation_role
        self._messages_list = []


    def append_new_message_to_conversation(self, new_message: Message):
        if new_message is None or not isinstance(new_message, Message):
            raise Exception(f"Invalid input to append_new_message_to_conversation, {type(new_message)}")

        self._messages_list.append(new_message)

    def get_messages_from_index(self, start_message_index:int = 0) -> list[Message]:
        if not isinstance(start_message_index, int) or len(self._messages_list) < start_message_index:
            raise IndexError(f"Got invalid index, max index for conversation is {len(self._messages_list)}, got {start_message_index}")

        selected_message = self._messages_list[start_message_index:].copy()

        return selected_message

    def get_messages_for_chat(self):
        messages_copy = self._messages_list.copy()
        selected_message = []
        for message in messages_copy:
            if not message.converser_ignore:
                selected_message.append(message)

        return selected_message

    def _delete_last_message(self) -> None:
        if len(self._messages_list) == 0:
            return

        self._messages_list.pop()