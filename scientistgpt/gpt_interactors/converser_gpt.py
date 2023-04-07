from typing import Optional, List

from scientistgpt.conversation.converation_manager import ConversationManager
from scientistgpt.proceed_retract import ProceedRetract, FuncAndRetractions


class ConverserGPT(ProceedRetract):
    """
    A base class for agents interacting logically with chatgpt to add and retract to a chat-conversation.

    Based on ProceedRetract, it allows going back upon to upstream states upon downstream failures.
    """
    OUTPUT_FILENAME = 'results.txt'
    ROLE = 'helpful scientist'

    def __init__(self,
                 run_plan: List[FuncAndRetractions] = None,
                 conversation_manager: Optional[ConversationManager] = None):
        super().__init__(run_plan)
        self.conversation_manager = conversation_manager

    def initialize_conversation(self):
        prompt = f'You are a {self.ROLE}.'
        self.conversation_manager = ConversationManager()
        self.conversation_manager.create_conversation()
        self.conversation_manager.append_system_message(prompt)
