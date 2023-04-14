import difflib
from dataclasses import dataclass

import colorama
from enum import Enum
from typing import NamedTuple, Optional

from scientistgpt.env import TEXT_WIDTH
from scientistgpt.run_gpt_code.code_runner import CodeRunner
from scientistgpt.utils.text_utils import format_text_with_code_blocks

# noinspection PyUnresolvedReferences
colorama.just_fix_windows_console()


class Role(str, Enum):
    SYSTEM = 'system'
    USER = 'user'
    ASSISTANT = 'assistant'
    SURROGATE = 'surrogate'
    COMMENTER = 'commenter'

    def is_assistant_or_surrogate(self):
        return self in [Role.ASSISTANT, Role.SURROGATE]

    def is_not_commenter(self):
        return self is not Role.COMMENTER


class ResponseStyle(NamedTuple):
    color: str
    code_color: str
    seperator: str


ROLE_TO_STYLE = {
    Role.SYSTEM: ResponseStyle(colorama.Fore.GREEN, colorama.Fore.LIGHTGREEN_EX, '-'),
    Role.USER: ResponseStyle(colorama.Fore.GREEN, colorama.Fore.LIGHTGREEN_EX, '-'),
    Role.ASSISTANT: ResponseStyle(colorama.Fore.CYAN, colorama.Fore.LIGHTCYAN_EX, '='),
    Role.SURROGATE: ResponseStyle(colorama.Fore.CYAN, colorama.Fore.LIGHTCYAN_EX, '='),
    Role.COMMENTER: ResponseStyle(colorama.Fore.BLUE, colorama.Fore.LIGHTBLUE_EX, ' '),
}


@dataclass(frozen=True)
class Message:
    role: Role
    content: str
    tag: str = ''

    def to_chatgpt_dict(self):
        return {'role': Role.ASSISTANT if self.role.is_assistant_or_surrogate() else self.role, 'content': self.content}

    def pretty_repr(self, number: Optional[int] = None, conversation_name: str = '', is_color: bool = True) -> str:
        """
        Returns a pretty repr of the message with color and heading.

        number: message sequential number in the conversation.

        Takes care of:
        * Indicating Role with name and color.
        * Adding separation lines
        * Indenting text
        * Highlighting code blocks
        """
        role, content, tag = self.role, self.content, self.tag
        tag_text = f'<{tag}> ' if tag else ''
        num_text = f'[{number}] ' if number else ''
        style = ROLE_TO_STYLE[role]
        sep = style.seperator
        if is_color:
            text_color, code_color, reset_color = style.color, style.code_color, colorama.Style.RESET_ALL
        else:
            text_color = code_color = reset_color = ''

        role_conversation_tag = f'{role.name} -> {conversation_name} {tag_text}'

        if role == Role.COMMENTER:
            return text_color + num_text + role_conversation_tag + ': ' + content + reset_color + '\n'

        # header:
        s = text_color + num_text + sep * (9 - len(num_text)) + ' ' + role_conversation_tag \
            + sep * (TEXT_WIDTH - len(role_conversation_tag) - 9 - 1) + '\n'

        # content:
        s += self.pretty_content(text_color, code_color, width=TEXT_WIDTH)

        # footer:
        s += text_color + sep * TEXT_WIDTH + reset_color
        return s

    def pretty_content(self, text_color, code_color, width):
        """
        Returns a pretty repr of just the message content.
        """
        return format_text_with_code_blocks(text=self.content, text_color=text_color,
                                            code_color=code_color, width=width)

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


@dataclass(frozen=True)
class CodeMessage(Message):
    """
    A message that contains code.
    """

    previous_code: str = None
    "The code from the previous response, to which this code should be compared"

    @property
    def extracted_code(self) -> str:
        """
        Extract the code from the response.
        """
        return CodeRunner(response=self.content).extract_code()

    def get_code_diff(self) -> str:
        """
        Get the difference between the code from the previous response and the code from this response.
        """
        diff = difflib.unified_diff(self.extracted_code, self.previous_code, lineterm='')
        return '\n'.join(diff)

    def pretty_content(self, text_color, code_color, width):
        """
        We override this method to replace the code within the message with the diff.
        """
        if self.previous_code:
            # we need to replace the code within the message with the diff
            diff = self.get_code_diff()
            content = self.content.replace(self.extracted_code, diff)
        else:
            content = self.content
        return format_text_with_code_blocks(content, text_color, code_color, width, is_python=True)


def create_message(role: Role, content: str, tag: str = '',
                   is_code: bool = False, previous_code: str = None) -> Message:
    if is_code:
        return CodeMessage(role=role, content=content, tag=tag, previous_code=previous_code)
    else:
        return Message(role=role, content=content, tag=tag)


def create_message_from_other_message(other_message: Message, content: str) -> Message:
    return create_message(role=other_message.role, content=content, tag=other_message.tag,
                          is_code=isinstance(other_message, CodeMessage),
                          previous_code=other_message.previous_code if isinstance(other_message, CodeMessage) else None)
