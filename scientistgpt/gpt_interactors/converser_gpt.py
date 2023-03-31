from typing import Optional, List

from scientistgpt.conversation import Conversation, Role
from scientistgpt.proceed_retract import ProceedRetract, FuncAndRetractions


class ConverserGPT(ProceedRetract):
    """
    Base class for an agent interacting with chatgpt
    """
    STATE_ATTRS: List[str] = ['conversation']
    OUTPUT_FILENAME = 'results.txt'
    ROLE = 'helpful scientist'

    def __init__(self,
                 run_plan: List[FuncAndRetractions] = None,
                 conversation: Optional[Conversation] = None):
        super().__init__(run_plan)
        self.conversation = conversation

    def initialize_conversation(self):
        prompt = f'You are a {self.ROLE}.'
        self.conversation = Conversation()
        self.conversation.append_message(Role.SYSTEM, prompt)
