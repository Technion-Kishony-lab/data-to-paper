from enum import Enum
from .env import OPENAI_API_KEY, MODEL_ENGINE

import openai

# Set up the OpenAI API client
openai.api_key = OPENAI_API_KEY


class Role(str, Enum):
    SYSTEM = 'system'
    USER = 'user'
    ASSISTANT = 'assistant'


class Conversation(list):
    """
    a list of message exchange between user and chatgtp.

    a Conversation instance allows:
    1. appending user queries.
    2. getting and appending chatgpt response.
    """

    @staticmethod
    def print_message(role: Role, message: str, should_print: bool = True):
        if should_print:
            print('----------------- ', role.value)
            print('\n' + message + '\n')

    def append_message(self, role: Role, message: str, should_print: bool = False):
        self.append({'role': role, 'content': message})
        self.print_message(role, message, should_print)

    def append_user_message(self, message: str, should_print: bool = True):
        self.append_message(role=Role.USER, message=message, should_print=should_print)

    def append_assistant_message(self, message: str, should_print: bool = True):
        self.append_message(role=Role.ASSISTANT, message=message, should_print=should_print)

    def get_response_from_chatgpt(self, should_print: bool = True, should_append: bool = True) -> str:
        response = openai.ChatCompletion.create(
            model=MODEL_ENGINE,
            messages=self,
        )
        response_message = response['choices'][0]['message']['content']
        if should_append:
            self.append_message(Role.ASSISTANT, response_message, should_print)
        return response_message

    def get_last_response(self):
        assert self[-1]['role'] == Role.ASSISTANT
        return self[-1]['content']
