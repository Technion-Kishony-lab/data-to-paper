import textwrap
from enum import Enum
from typing import NamedTuple

from scientistgpt.env import OPENAI_API_KEY, MODEL_ENGINE

import openai
import colorama

# Set up the OpenAI API client
from scientistgpt.utils import wrap_string

openai.api_key = OPENAI_API_KEY

# noinspection PyUnresolvedReferences
colorama.just_fix_windows_console()


class ResponseStyle(NamedTuple):
    color: str
    seperator: str


USER_STYLE = ResponseStyle(colorama.Fore.GREEN, '-')
ASSISTANT_STYLE = ResponseStyle(colorama.Fore.CYAN, '=')
TEXT_WIDTH = 120


class Role(str, Enum):
    SYSTEM = 'system'
    USER = 'user'
    ASSISTANT = 'assistant'


class Conversation(list):
    """

    Maintain a list of message exchange between user and chatgpt.
    Takes care of adding messages and communicating with openai, including:

    1. appending user queries.
    2. getting and appending chatgpt response.
    3. print colored-styled messages of user and assistant.
    """

    @staticmethod
    def print_message(role: Role, message: str, should_print: bool = True):
        if not should_print:
            return
        style = ASSISTANT_STYLE if role is Role.ASSISTANT else USER_STYLE
        sep = style.seperator
        print()
        print(style.color + sep * 7 + ' ' + role.name + ' ' + sep * (TEXT_WIDTH - len(role.name) - 9))
        print(wrap_string(message, width=TEXT_WIDTH))
        print(sep * TEXT_WIDTH, colorama.Style.RESET_ALL)

    def append_message(self, role: Role, message: str, should_print: bool = False):
        self.append({'role': role, 'content': message})
        self.print_message(role, message, should_print)

    def append_user_message(self, message: str, should_print: bool = True):
        self.append_message(role=Role.USER, message=message, should_print=should_print)

    def append_assistant_message(self, message: str, should_print: bool = True):
        self.append_message(role=Role.ASSISTANT, message=message, should_print=should_print)

    def _get_chatgpt_completion(self):
        # We start with the entire conversation, but if we get an exception from openai, we gradually remove old
        # prompts.
        for starting_index in range(len(self)):
            try:
                return openai.ChatCompletion.create(
                    model=MODEL_ENGINE,
                    messages=self[starting_index:],
                )
            except openai.error.InvalidRequestError as e:
                pass
        raise e

    def get_response_from_chatgpt(self, should_print: bool = True, should_append: bool = True) -> str:
        response = self._get_chatgpt_completion()
        response_message = response['choices'][0]['message']['content']
        if should_append:
            self.append_message(Role.ASSISTANT, response_message, should_print)
        return response_message

    def get_last_response(self):
        assert self[-1]['role'] == Role.ASSISTANT
        return self[-1]['content']
