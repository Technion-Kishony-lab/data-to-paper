import copy
import re
from enum import Enum
from typing import NamedTuple, TypedDict

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


TEXT_WIDTH = 120

# Use unique patterns, not likely to occur in conversation:
SAVE_START = '>>>>> '
SAVE_END = '\n<<<<<\n'


class Role(str, Enum):
    SYSTEM = 'system'
    USER = 'user'
    ASSISTANT = 'assistant'
    COMMENTER = 'commenter'


ROLE_TO_STYLE = {
    Role.SYSTEM: ResponseStyle(colorama.Fore.GREEN, colorama.Fore.LIGHTGREEN_EX, '-'),
    Role.USER: ResponseStyle(colorama.Fore.GREEN, colorama.Fore.LIGHTGREEN_EX, '-'),
    Role.ASSISTANT: ResponseStyle(colorama.Fore.CYAN, colorama.Fore.LIGHTCYAN_EX, '='),
    Role.COMMENTER: ResponseStyle(colorama.Fore.RED, colorama.Fore.LIGHTRED_EX, ''),
}


class Message(TypedDict):
    role: Role
    content: str


class Conversation(list[Message]):
    """

    Maintain a list of message exchange between user and chatgpt.
    Takes care of adding messages and communicating with openai, including:

    1. appending user queries.
    2. getting and appending chatgpt response.
    3. print colored-styled messages of user and assistant.
    4. save/load messages as text file.
    """

    @staticmethod
    def print_message(message: Message, should_print: bool = True):
        if not should_print:
            return
        role, content = message['role'], message['content']
        style = ROLE_TO_STYLE[role]
        sep = style.seperator
        if role is not Role.COMMENTER:
            print(style.color + sep * 7 + ' ' + role.name + ' ' + sep * (TEXT_WIDTH - len(role.name) - 9))
        print_wrapped_text_with_code_blocks(text=content, text_color=style.color,
                                            code_color=style.code_color, width=TEXT_WIDTH)
        print(style.color + sep * TEXT_WIDTH, colorama.Style.RESET_ALL)
        print()

    def append_message(self, role: Role, content: str, should_print: bool = False):
        message = Message(role=role, content=content)
        self.append(message)
        self.print_message(message, should_print)

    def append_user_message(self, content: str, should_print: bool = True):
        self.append_message(role=Role.USER, content=content, should_print=should_print)

    def append_assistant_message(self, content: str, should_print: bool = True):
        self.append_message(role=Role.ASSISTANT, content=content, should_print=should_print)

    def add_comment(self, content: str, should_print: bool = True):
        self.append_message(role=Role.COMMENTER, content=content, should_print=should_print)

    def get_messages_without_comments(self):
        return [message for message in self if message['role'] is not Role.COMMENTER]

    def _get_chatgpt_completion(self):
        # We start with the entire conversation, but if we get an exception from openai, we gradually remove old
        # prompts.
        # TODO: this solution is SLOW. Better figure out in advance how many messages are ok to send to openai.
        messages = self.get_messages_without_comments()
        for starting_index in range(len(messages)):
            try:
                return openai.ChatCompletion.create(
                    model=MODEL_ENGINE,
                    messages=messages[starting_index:],
                )
            except openai.error.InvalidRequestError:
                print_red(f'InvalidRequestError, when sending messages {starting_index} - {len(messages)}.\n'
                          f'Retrying with messages {starting_index + 1} - {len(messages)}')
        raise RuntimeError("Cannot get openai response.")

    def get_response_from_chatgpt(self, should_print: bool = True, should_append: bool = True) -> str:
        response = self._get_chatgpt_completion()
        response_content = response['choices'][0]['message']['content']
        if should_append:
            self.append_assistant_message(response_content, should_print)
        return response_content

    def get_last_response(self):
        assert self[-1]['role'] == Role.ASSISTANT
        return self[-1]['content']

    def delete_last_response(self):
        assert self[-1]['role'] == Role.ASSISTANT
        self.pop()

    def save(self, filename: str):
        with open(filename, 'w') as f:
            for message in self:
                f.write(SAVE_START + message['role'] + '\n')
                f.write(message['content'])
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
        for message in self:
            self.print_message(message)
