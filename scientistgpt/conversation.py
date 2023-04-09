import copy
import re
from enum import Enum
from typing import NamedTuple, Optional, Callable

from scientistgpt.env import OPENAI_API_KEY, MODEL_ENGINE
from scientistgpt.utils.text_utils import print_wrapped_text_with_code_blocks, print_red

import openai
import colorama

# Set up the OpenAI API client
openai.api_key = OPENAI_API_KEY

# noinspection PyUnresolvedReferences
colorama.just_fix_windows_console()


class ResponseStyle(NamedTuple):
    color: str
    code_color: str
    seperator: str


USER_STYLE = ResponseStyle(colorama.Fore.GREEN, colorama.Fore.LIGHTGREEN_EX, '-')
ASSISTANT_STYLE = ResponseStyle(colorama.Fore.CYAN, colorama.Fore.LIGHTCYAN_EX, '=')
TEXT_WIDTH = 120

# Use unique patterns, not likely to occur in conversation:
SAVE_START = '>>>>> '
SAVE_END = '\n<<<<<\n'


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
    4. save/load messages as text file.
    """

    def __init__(self, message_callback: Optional[Callable] = None, **kwargs):
        super().__init__(**kwargs)
        self.message_callback = message_callback

    def __deepcopy__(self, memo):
        new_instance = Conversation()
        for message in self:
            new_instance.append_message(message['role'], message['content'], should_print=False)
        new_instance.message_callback = self.message_callback
        return new_instance

    def print_message(self, role: Role, message: str, should_print: bool = True):
        if not should_print:
            return
        style = ASSISTANT_STYLE if role is Role.ASSISTANT else USER_STYLE
        sep = style.seperator
        print(style.color + sep * 7 + ' ' + role.name + ' ' + sep * (TEXT_WIDTH - len(role.name) - 9))
        print_wrapped_text_with_code_blocks(text=message, text_color=style.color,
                                            code_color=style.code_color, width=TEXT_WIDTH)
        print(style.color + sep * TEXT_WIDTH, colorama.Style.RESET_ALL)
        print()

        if self.message_callback:
            self.message_callback(role, message)

    def append_message(self, role: Role, message: str, should_print: bool = False):
        self.append({'role': role, 'content': message})
        self.print_message(role, message, should_print)

    def append_user_message(self, message: str, should_print: bool = True):
        self.append_message(role=Role.USER, message=message, should_print=should_print)

    def append_assistant_message(self, message: str, should_print: bool = True):
        self.append_message(role=Role.ASSISTANT, message=message, should_print=should_print)

    def _get_chatgpt_completion(self, **kwargs) -> dict:
        # We start with the entire conversation, but if we get an exception from openai, we gradually remove old
        # prompts.
        # TODO: this solution is SLOW. Better figure out in advance how many messages are ok to send to openai.
        for starting_index in range(len(self)):
            try:
                return openai.ChatCompletion.create(
                    model=MODEL_ENGINE,
                    messages=self[starting_index:],
                    **kwargs,
                )
            except openai.error.InvalidRequestError:
                print_red(f'InvalidRequestError, when sending messages {starting_index} - {len(self)}.\n'
                          f'Retrying with messages {starting_index + 1} - {len(self)}' , message_callback=self.message_callback)
        raise RuntimeError("Cannot get openai response.")

    def get_response_from_chatgpt(self, should_print: bool = True, should_append: bool = True, **kwargs) -> str:
        response = self._get_chatgpt_completion(**kwargs)
        response_message = response['choices'][0]['message']['content']
        if should_append:
            self.append_message(Role.ASSISTANT, response_message, should_print)
        return response_message

    def get_last_response(self):
        assert self[-1]['role'] == Role.ASSISTANT
        return self[-1]['content']

    def delete_last_response(self):
        assert self[-1]['role'] == Role.ASSISTANT
        self.pop()

    def save(self, filename: str):
        with open(filename, 'w') as f:
            for exchange in self:
                role = exchange['role']
                message = exchange['content']
                f.write(SAVE_START + role + '\n')
                f.write(message)
                f.write(SAVE_END + '\n\n')

    def load(self, filename: str):
        self.clear()
        with open(filename, 'r') as f:
            entire_file = f.read()
            matches = re.findall(SAVE_START + "(.*?)" + SAVE_END, entire_file, re.DOTALL)
            for match in matches:
                first_break = match.index('\n')
                role = Role(match[:first_break])

                message = match[first_break + 1:]
                self.append_message(role, message)

    @classmethod
    def from_file(cls, filename: str):
        self = cls()
        self.load(filename)
        return self

    def print_all_messages(self):
        for exchange in self:
            self.print_message(exchange['role'], exchange['content'])
