from dataclasses import dataclass
from typing import Optional

from data_to_paper_new.chatgpt_client.chatgpt_models import ChatGptRole


@dataclass
class Message:
    """
    A class that represent a message between chatgpt and the client
    """
    request_content: str
    response_content: Optional[str] = None
    tag: str = ''
    converser_ignore: bool = False  # if True, this message will be skipped when calling openai
    is_background: bool = False
    
    def __init__(self, request_content: str):
        self.request_content = request_content
        

    def to_chatgpt_messages(self) -> list[dict]:

        chatgpt_messages = [{"role": ChatGptRole.USER.value, "content": self.request_content}]

        if self.response_content is not None:
            chatgpt_messages.append({"role": ChatGptRole.ASSISTANT.value, "content": self.response_content})

        return chatgpt_messages



