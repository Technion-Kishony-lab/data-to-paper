import colorama
from enum import Enum
from typing import NamedTuple, Optional

from scientistgpt.env import TEXT_WIDTH
from scientistgpt.utils.text_utils import print_wrapped_text_with_code_blocks

# noinspection PyUnresolvedReferences
colorama.just_fix_windows_console()


class Role(str, Enum):
    SYSTEM = 'system'
    USER = 'user'
    ASSISTANT = 'assistant'
    COMMENTER = 'commenter'


class ResponseStyle(NamedTuple):
    color: str
    code_color: str
    seperator: str


ROLE_TO_STYLE = {
    Role.SYSTEM: ResponseStyle(colorama.Fore.GREEN, colorama.Fore.LIGHTGREEN_EX, '-'),
    Role.USER: ResponseStyle(colorama.Fore.GREEN, colorama.Fore.LIGHTGREEN_EX, '-'),
    Role.ASSISTANT: ResponseStyle(colorama.Fore.CYAN, colorama.Fore.LIGHTCYAN_EX, '='),
    Role.COMMENTER: ResponseStyle(colorama.Fore.RED, colorama.Fore.LIGHTRED_EX, ' '),
}


class Message(NamedTuple):
    role: Role
    content: str
    tag: str = ''

    def to_chatgpt_dict(self):
        return {'role': self.role, 'content': self.content}

    def display(self, number: Optional[int] = None):
        """
        Display the message with color and heading.

        number: message sequential number in the conversation.

        Takes care of:
        * Indicating Role with name and color.
        * Adding separation lines
        * Indenting text
        * Highlighting code blocks
        """
        role, content, tag = self
        tag_text = f'({tag}) ' if tag else ''
        num_text = f'[{number}] ' if number else ''
        style = ROLE_TO_STYLE[role]
        sep = style.seperator
        print(style.color + num_text + sep * (9 - len(num_text)) + ' ' + role.name + ' ' + tag_text
              + sep * (TEXT_WIDTH - len(role.name) - len(tag_text) - 9 - 2))
        print_wrapped_text_with_code_blocks(text=content, text_color=style.color,
                                            code_color=style.code_color, width=TEXT_WIDTH)
        print(style.color + sep * TEXT_WIDTH, colorama.Style.RESET_ALL)

    def convert_to_text(self):
        return f'{self.role}<{self.tag}>\n{self.content}'

    @classmethod
    def from_text(cls, text):
        first_break = text.index('\n')
        first_lt = text.index('<')
        role = Role(text[:first_lt])
        tag = text[first_lt + 1: first_break - 1]
        content = text[first_break + 1:]
        return cls(role=role, content=content, tag=tag)
