import difflib
from dataclasses import dataclass

import colorama
from enum import Enum
from typing import NamedTuple, Optional

from scientistgpt.env import TEXT_WIDTH, MINIMAL_COMPACTION_TO_SHOW_CODE_DIFF, HIDE_INCOMPLETE_CODE
from scientistgpt.cast import Agent
from scientistgpt.run_gpt_code.code_runner import CodeRunner
from scientistgpt.run_gpt_code.exceptions import FailedExtractingCode
from scientistgpt.utils import format_text_with_code_blocks, line_count

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
    agent: Optional[Agent] = None
    ignore: bool = False  # if True, this message will be skipped when calling openai

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
        role, content, tag, agent = self.role, self.content, self.tag, self.agent
        tag_text = f' <{tag}> ' if tag else ''
        agent_text = f' {{{agent}}}' if agent else ''
        num_text = f'[{number}] ' if number else ''
        style = ROLE_TO_STYLE[role]
        sep = style.seperator
        if is_color:
            text_color, code_color, reset_color = style.color, style.code_color, colorama.Style.RESET_ALL
        else:
            text_color = code_color = reset_color = ''

        if role == Role.SYSTEM:
            role_agent_conversation_tag = f'{role.name} casting {agent_text} for {conversation_name}'
        else:
            role_agent_conversation_tag = f'{role.name}{agent_text} -> {conversation_name}{tag_text}'

        if role == Role.COMMENTER:
            return text_color + num_text + role_agent_conversation_tag + ': ' + content + reset_color

        # header:
        s = text_color + num_text + sep * (9 - len(num_text)) + ' ' + role_agent_conversation_tag \
            + sep * (TEXT_WIDTH - len(role_agent_conversation_tag) - 9 - 1) + '\n'

        # content:
        s += self.pretty_content(text_color, code_color, width=TEXT_WIDTH)
        if s[-1] != '\n':
            s += '\n'

        # footer:
        s += text_color + sep * TEXT_WIDTH + reset_color
        return s

    def pretty_content(self, text_color, code_color, width):
        """
        Returns a pretty repr of just the message content.
        """
        return format_text_with_code_blocks(text=self.content.strip(), text_color=text_color,
                                            code_color=code_color, width=width, is_python=False)

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
    def extracted_code(self) -> Optional[str]:
        """
        Extract the code from the response.
        """
        try:
            return CodeRunner(response=self.content).extract_code()
        except FailedExtractingCode:
            return None

    def get_code_diff(self) -> str:
        """
        Get the difference between the code from the previous response and the code from this response.
        """
        diff = difflib.unified_diff(self.previous_code.strip().splitlines(),
                                    self.extracted_code.strip().splitlines(),
                                    lineterm='', n=0)
        # we remove the first 3 lines, which are the header of the diff:
        diff = list(diff)[3:]
        return '\n'.join(diff)

    def pretty_content(self, text_color, code_color, width):
        """
        We override this method to replace the code within the message with the diff.
        """
        content = self.content
        if self.extracted_code:
            if self.previous_code:
                diff = self.get_code_diff()
                if line_count(self.extracted_code) - line_count(diff) > MINIMAL_COMPACTION_TO_SHOW_CODE_DIFF:
                    # if the code diff is substantially shorter than the code, we replace the code with the diff:
                    content = content.replace(
                        self.extracted_code,
                        "# FULL CODE SENT BY CHATGPT IS SHOWN AS A DIFF WITH PREVIOUS CODE\n" + diff if diff
                        else "# CHATGPT SENT THE SAME CODE AS BEFORE\n")
        elif HIDE_INCOMPLETE_CODE:
            # if we failed to extract the code, we check if there is a single incomplete code replace
            # and replace it with a message:
            sections = self.content.split('```')
            if len(sections) == 2:
                partial_code = sections[1]
                content = content.replace(
                    partial_code,
                    f"\n# NOT SHOWING {line_count(partial_code)} LINES OF INCOMPLETE CODE SENT BY CHATGPT\n```\n")

        return format_text_with_code_blocks(content, text_color, code_color, width, is_python=True)


def create_message(role: Role, content: str, tag: str = '', agent: Optional[Agent] = None, ignore: bool = False,
                   is_code: bool = False, previous_code: str = None) -> Message:
    if is_code:
        return CodeMessage(role=role, content=content, tag=tag, agent=agent, ignore=ignore, previous_code=previous_code)
    else:
        return Message(role=role, content=content, tag=tag, agent=agent, ignore=ignore)


def create_message_from_other_message(other_message: Message, content: str) -> Message:
    return create_message(role=other_message.role, content=content, tag=other_message.tag, agent=other_message.agent,
                          ignore=other_message.ignore,
                          is_code=isinstance(other_message, CodeMessage),
                          previous_code=other_message.previous_code if isinstance(other_message, CodeMessage) else None)
