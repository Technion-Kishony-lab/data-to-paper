from dataclasses import dataclass
from typing import Optional, List

from scientistgpt.conversation.converation_manager import ConversationManager
from scientistgpt.proceed_retract import ProceedRetract, FuncAndRetractions


@dataclass
class ConverserGPT:
    """
    A base class for agents interacting with chatgpt.
    """

    system_prompt = 'You are a helpful scientist.'

    conversation_name = 'default'

    def __post_init__(self):
        self.conversation_manager = ConversationManager(conversation_name=self.conversation_name)

    @property
    def conversation(self):
        return self.conversation_manager.conversation

    def initialize_conversation(self):
        self.conversation_manager.create_conversation()
        self.conversation_manager.append_system_message(self.system_prompt)


@dataclass
class DialogConverserGPT(ConverserGPT):
    """
    A base class for agents running a dialog between two chatgpts.
    """

    other_system_prompt: str = 'You are a helpful scientist.'

    other_conversation_name: str = 'other'

    def __post_init__(self):
        super().__post_init__()
        self.other_conversation_manager = ConversationManager(conversation_name=self.other_conversation_name)

    @property
    def other_conversation(self):
        return self.other_conversation_manager.conversation

    def initialize_other_conversation(self):
        self.other_conversation_manager.create_conversation()
        self.other_conversation_manager.append_system_message(self.system_prompt)


@dataclass
class CodeWritingGPT(ConverserGPT):
    """
    Interact with chatgpt to write a code that needs to create an output file.
    """

    output_filename = 'results.txt'
    """
    The name of the file that gpt code is instructed to save the results to.
    """

    gpt_script_filename = 'gpt_code'
    """
    The base name of the pythin file in which the code written by gpt is saved. 
    """


