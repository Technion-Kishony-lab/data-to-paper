from __future__ import annotations
import openai
import re
from typing import List, Tuple, Union, Optional, Set

from .message import Message, Role
from .message_designation import GeneralMessageDesignation, convert_general_message_designation_to_int_list

# Set up the OpenAI API client
from g3pt.env import OPENAI_API_KEY, MODEL_ENGINE
from g3pt.call_servers import ServerCaller

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from g3pt.cast import Agent


openai.api_key = OPENAI_API_KEY

# String patterns used to save and load conversations. Use unique patterns, not likely to occur in conversation.
SAVE_START = 'START>>>>>\n'
SAVE_END = '\n<<<<<END\n'


class OpenaiSeverCaller(ServerCaller):
    """
    Class to call OpenAI API.
    """
    file_extension = '_openai.txt'

    @staticmethod
    def _save_records(file, records):
        for response in records:
            file.write(f'{SAVE_START}{response}{SAVE_END}\n')

    @staticmethod
    def _load_records(file):
        return re.findall(SAVE_START + "(.*?)" + SAVE_END, file.read(), re.DOTALL)

    @staticmethod
    def _get_server_response(messages: List[Message], **kw) -> str:
        """
        Connect with openai to get response to conversation.
        """
        response = openai.ChatCompletion.create(
            model=MODEL_ENGINE,
            messages=[message.to_chatgpt_dict() for message in messages],
            **kw,
        )
        return response['choices'][0]['message']['content']


OPENAI_SERVER_CALLER = OpenaiSeverCaller()


class Conversation(List[Message]):
    """
    Maintain a list of messages as exchanged between user and chatgpt.

    Takes care of:

    1. save/load to text.
    2. print colored-styled messages.

    DO NOT ALTER CONVERSATION INSTANCE DIRECTLY. USE `ConversationManager` INSTEAD.
    """

    def __init__(self, *args, conversation_name: Optional[str] = None,
                 participants: Optional[Set[Agent]] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.conversation_name = conversation_name
        self.participants = participants  # None - do not enforce participants

    def add_participant(self, agent: Agent):
        if self.participants is None:
            self.participants = []
        self.participants.add(agent)

    def remove_participant(self, agent: Agent):
        if self.participants is not None:
            self.participants.remove(agent)

    def append(self, message: Message):
        if self.participants is not None and message.role is not Role.COMMENTER:
            assert message.agent in self.participants, f'Agent {message.agent} not in conversation participants.'
        super().append(message)

    def get_chosen_indices_and_messages(self, hidden_messages: GeneralMessageDesignation = None
                                        ) -> List[Tuple[int, Message]]:
        """
        Return sub-list of messages.
        Remove commenter messages, ignore=True messages, as well as all messages indicated in `hidden_messages`.
        """
        hidden_messages = hidden_messages or []
        hidden_messages = convert_general_message_designation_to_int_list(hidden_messages, self)
        return [(i, message) for i, message in enumerate(self)
                if i not in hidden_messages
                and message.role is not Role.COMMENTER
                and not message.ignore]

    def get_last_response(self) -> str:
        """
        Return the last response from the assistant.

        will skip over any COMMENTER messages.
        """
        last_non_commenter_message = self.get_last_non_commenter_message()
        assert last_non_commenter_message.role.is_assistant_or_surrogate()
        return last_non_commenter_message.content

    def get_last_non_commenter_message(self) -> Message:
        """
        Return the last non-commenter message.
        """
        for i in range(len(self) - 1, -1, -1):
            if self[i].role is not Role.COMMENTER:
                return self[i]
        raise ValueError('No non-commenter message found.')

    def get_message_content_by_tag(self, tag):
        for message in self:
            if message.tag == tag:
                return message.content
        return None

    def delete_last_response(self):
        assert self[-1].role.is_assistant_or_surrogate()
        self.pop()

    def save(self, filename: str):
        with open(filename, 'w') as f:
            for message in self:
                f.write(f'{SAVE_START}{message.convert_to_text()}{SAVE_END}\n\n')

    def load(self, filename: str):
        self.clear()
        with open(filename, 'r') as f:
            entire_file = f.read()
            matches = re.findall(SAVE_START + "(.*?)" + SAVE_END, entire_file, re.DOTALL)
            for match in matches:
                self.append(Message.from_text(match))

    @classmethod
    def from_file(cls, filename: str):
        self = cls()
        self.load(filename)
        return self

    def print_all_messages(self):
        for message in self:
            print(message.pretty_repr())
            print()

    def try_get_chatgpt_response(self, hidden_messages: GeneralMessageDesignation = None,
                                 **kwargs) -> Union[str, Exception]:
        """
        Try to get a response from openai to a specified conversation.

        The conversation is sent to openai after removing comment messages and any messages indicated
        in `hidden_messages`.

        If getting a response is successful then return response string.
        If failed due to openai exception, return None.
        """
        indices_and_messages = self.get_chosen_indices_and_messages(hidden_messages)
        messages = [message for _, message in indices_and_messages]
        try:
            return OPENAI_SERVER_CALLER.get_server_response(messages, **kwargs)
        except openai.error.InvalidRequestError as e:
            return e
        except Exception:
            raise RuntimeError("Failed accessing openai.")
