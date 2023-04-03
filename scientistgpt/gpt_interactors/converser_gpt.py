from typing import Optional, List
import abc
from scientistgpt.conversation import Conversation, Role
from scientistgpt.proceed_retract import ProceedRetract, FuncAndRetractions


class ConverserGPT(ProceedRetract):
    """
    A base class for agents interacting logically with chatgpt to add and retract to a chat-conversation.

    Based on ProceedRetract, it allows going back upon to upstream states upon downstream failures.
    """
    STATE_ATTRS: List[str] = ['conversation']
    OUTPUT_FILENAME = 'results.txt'
    ROLE = 'helpful scientist'

    def __init__(self,
                 run_plan: List[FuncAndRetractions] = None,
                 conversation: Optional[Conversation] = None):
        super().__init__(run_plan)
        self.conversation = conversation

    # define initialize abstract method to be implemented by subclasses

    @abc.abstractmethod
    def initialize_conversation(self):
        prompt = f'You are a {self.ROLE}.'
        self.conversation = Conversation()
        self.conversation.append_message(Role.SYSTEM, prompt, should_print=True)