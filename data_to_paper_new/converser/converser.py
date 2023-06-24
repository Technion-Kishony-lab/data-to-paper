from dataclasses import dataclass, field
from enum import Enum

from data_to_paper_new.chatgpt_client.chatgpt_models import ChatGptRole
from data_to_paper_new.roles.base_role import Role
from data_to_paper_new.chatgpt_client.gpt_client import ChatGptClient
from data_to_paper_new.conversation.conversation import Conversation
from data_to_paper_new.conversation.message import Message


class RequestHistoryTypes(Enum):
    ALL_CHAT_HISTORY = 1,
    NO_HISTORY = 2


class Conversor:
    conversation: Conversation
    chatgpt_client: ChatGptClient
    chatgpt_role: Role

    def __init__(self, conversation_name: str, chatgpt_role: Role, chatgpt_client: ChatGptClient):
        self.chatgpt_role = chatgpt_role
        self.conversation = Conversation(conversation_name, chatgpt_role)
        self.chatgpt_client = chatgpt_client


    #Split to more function
    def query_chatgpt(self, request_history: RequestHistoryTypes, message_content: str) -> str:
        messages_for_request = []
        messages_for_request.extend(self._get_relevant_history(request_history))

        new_message = Message(message_content)
        messages_for_request.append(new_message)

        # Generate initial prompt
        chatgpt_messages = [{"role": ChatGptRole.SYSTEM.value, "content": self.chatgpt_role.generate_prompt()}]

        for message in messages_for_request:
            chatgpt_messages.extend(self._message_to_chatgpt_messages(message))

        try:
            chatgpt_response = self.chatgpt_client.get_response_for_messages(chatgpt_messages)
            new_message.response_content = chatgpt_response
            self.conversation.append_new_message_to_conversation(new_message)

            return chatgpt_response

        except Exception as e:
            print(e)
            raise

    # Should be overloaded
    def _get_relevant_history(self, request_history: RequestHistoryTypes) -> list[Message]:
        history_messages = []
        if request_history == RequestHistoryTypes.NO_HISTORY:
            pass
        elif request_history == RequestHistoryTypes.ALL_CHAT_HISTORY:
            history_messages.extend(self.conversation.get_messages_for_chat())

        return history_messages


    def regenerate_last_response(self) -> str:
        last_message = self.conversation.pop_last_message()
        regenerated_output = self.query_chatgpt(RequestHistoryTypes.ALL_CHAT_HISTORY, last_message.request_content)

        return regenerated_output

    def replace_last_response(self, new_response_content: str) -> None:
        last_message = self.conversation.pop_last_message()
        last_message.response_content = new_response_content
        self.conversation.append_new_message_to_conversation(last_message)


    @staticmethod
    def _message_to_chatgpt_messages(message: Message) -> list[dict]:
        if not isinstance(message, Message):
            raise Exception(f"Expected Message, got {type(message)}")

        chatgpt_messages = [{"role": ChatGptRole.USER.value, "content": message.request_content}]

        if message.response_content is not None:
            chatgpt_messages.append({"role": ChatGptRole.ASSISTANT.value, "content": message.response_content})

        return chatgpt_messages
