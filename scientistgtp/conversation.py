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
    2. getting and appending gpt response.
    """
    @staticmethod
    def print_message(message: str, should_print: bool = True):
        if should_print:
            print('-----------------')
            print('\n' + message + '\n')

    def append_message(self, role: Role, message: str, should_print: bool = False):
        self.append({'role': role, 'content': message})
        self.print_message(message, should_print)

    def get_response(self,
                     should_print: bool = True,
                     should_append: bool = True) -> str:
        response = openai.ChatCompletion.create(
            model=MODEL_ENGINE,
            messages=self,
        )
        response_message = response['choices'][0]['message']['content']
        if should_append:
            self.append_message(Role.ASSISTANT, response_message)
        self.print_message(response_message, should_print)
        return response_message
