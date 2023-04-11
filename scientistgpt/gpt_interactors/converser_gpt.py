from dataclasses import dataclass

from scientistgpt.conversation.converation_manager import ConversationManager


@dataclass
class ConverserGPT:
    """
    A base class for agents interacting with chatgpt.
    """

    system_prompt: str = 'You are a helpful scientist.'

    conversation_name: str = 'default'

    agent: str = ''

    def __post_init__(self):
        self.conversation_manager = ConversationManager(
            conversation_name=self.conversation_name,
            agent=self.agent
        )

    @property
    def _system_prompt(self):
        return self.system_prompt

    @property
    def conversation(self):
        return self.conversation_manager.conversation

    def initialize_conversation_if_needed(self):
        if self.conversation_manager.conversation is None:
            self.conversation_manager.create_conversation()
        if len(self.conversation) == 0:
            self.conversation_manager.append_system_message(self._system_prompt)


@dataclass
class CodeWritingGPT(ConverserGPT):
    """
    Interact with chatgpt to write a code that needs to create an output file.
    """

    output_filename: str = 'results.txt'
    """
    The name of the file that gpt code is instructed to save the results to.
    """

    gpt_script_filename: str = 'gpt_code'
    """
    The base name of the pythin file in which the code written by gpt is saved. 
    """
