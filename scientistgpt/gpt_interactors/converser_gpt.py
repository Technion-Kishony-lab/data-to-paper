from dataclasses import dataclass, field
from typing import Optional, List

from scientistgpt.conversation.converation_manager import ConversationManager
from scientistgpt.conversation.message_designation import GeneralMessageDesignation
from scientistgpt.data_file_description import DataFileDescription
from scientistgpt.utils.text_utils import print_red, NiceList

from scientistgpt.cast import Agent


@dataclass
class ConverserGPT:
    """
    A base class for agents interacting with chatgpt.
    """

    system_prompt: str = 'You are a helpful scientist.'

    assistant_agent: Agent = Agent.Student
    user_agent: Agent = Agent.Mentor

    conversation_name: str = 'default'

    driver: str = ''

    def __post_init__(self):
        self.conversation_manager = ConversationManager(
            conversation_name=self.conversation_name,
            driver=self.driver if self.driver is not None else type(self).__name__,
            assistant_agent=self.assistant_agent,
            user_agent=self.user_agent,
        )

    @property
    def actual_system_prompt(self):
        return self.system_prompt

    @property
    def conversation(self):
        return self.conversation_manager.conversation

    def initialize_conversation_if_needed(self):
        self.conversation_manager.initialize_conversation_if_needed()
        if len(self.conversation) == 0:
            self.apply_append_system_message(self.actual_system_prompt)

    def comment(self, comment: str, tag: Optional[str] = None, as_action: bool = True):
        """
        Print a comment, either directly, or as an action appending a COMMENTER message to the conversation (default).
        """
        if as_action:
            self.conversation_manager.append_commenter_message(comment, tag=tag)
        else:
            print_red(comment)

    def apply_get_and_append_assistant_message(self, tag: Optional[str] = None, comment: Optional[str] = None,
                                               previous_code: Optional[str] = None,
                                               hidden_messages: GeneralMessageDesignation = None, **kwargs) -> str:
        return self.conversation_manager.get_and_append_assistant_message(tag=tag, comment=comment,
                                                                          previous_code=previous_code,
                                                                          hidden_messages=hidden_messages, **kwargs)

    def apply_append_user_message(self, content: str, tag: Optional[str] = None, comment: Optional[str] = None,
                                  previous_code: Optional[str] = None):
        return self.conversation_manager.append_user_message(content, tag=tag, comment=comment,
                                                             previous_code=previous_code)

    def apply_append_system_message(self, content: str, tag: Optional[str] = None, comment: Optional[str] = None):
        return self.conversation_manager.append_system_message(content, tag=tag, comment=comment)

    def apply_append_surrogate_message(self, content: str, tag: Optional[str] = None, comment: Optional[str] = None,
                                       previous_code: Optional[str] = None):
        return self.conversation_manager.append_surrogate_message(content, tag=tag, comment=comment,
                                                                  previous_code=previous_code)


@dataclass
class CodeWritingGPT(ConverserGPT):
    """
    Interact with chatgpt to write a code that needs to create an output file.
    """

    output_filename: str = 'results.txt'
    "The name of the file that gpt code is instructed to save the results to."

    gpt_script_filename: str = 'gpt_code'
    "The base name of the pythin file in which the code written by gpt is saved."

    data_file_descriptions: List[DataFileDescription] = field(default_factory=list)
    "A list of data file descriptions that are used by the code."

    @property
    def data_files(self) -> List[str]:
        return NiceList([d.file_path for d in self.data_file_descriptions],
                        wrap_with='"',
                        prefix='{} data file[s]: ')
