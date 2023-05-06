from dataclasses import dataclass
from typing import Optional, ClassVar

from scientistgpt.conversation import ConversationManager, GeneralMessageDesignation
from scientistgpt.conversation.stage import Stage
from scientistgpt.servers.openai_models import ModelEngine
from scientistgpt.utils.replacer import Replacer, with_attribute_replacement
from scientistgpt.utils.text_utils import print_red
from scientistgpt.base_cast import Agent


@dataclass
class ConverserGPT(Replacer):
    """
    A base class for agents interacting with chatgpt.
    """
    model_engine: ClassVar[ModelEngine] = None
    """
    The openai model engine to use. If None, use the default model engine.
    A call to apply_get_and_append_assistant_message can override this value.
    """

    system_prompt: str = 'You are a helpful scientist.'

    assistant_agent: Agent = None
    user_agent: Agent = None

    conversation_name: str = 'default'

    driver: str = ''

    @with_attribute_replacement
    def __post_init__(self):
        self.conversation_manager = ConversationManager(
            conversation_name=self.conversation_name,
            driver=self.driver if self.driver is not None else type(self).__name__,
            assistant_agent=self.assistant_agent,
            user_agent=self.user_agent,
        )

    @property
    def conversation(self):
        return self.conversation_manager.conversation

    @with_attribute_replacement
    def initialize_conversation_if_needed(self):
        self.conversation_manager.initialize_conversation_if_needed()
        if len(self.conversation) == 0:
            self.apply_append_system_message(self.system_prompt)

    def comment(self, comment: str, tag: Optional[str] = None, as_action: bool = True):
        """
        Print a comment, either directly, or as an action appending a COMMENTER message to the conversation (default).
        """
        if as_action:
            self.conversation_manager.append_commenter_message(comment, tag=tag)
        else:
            print_red(comment)

    def apply_get_and_append_assistant_message(self, tag: Optional[str] = None, comment: Optional[str] = None,
                                               is_code: bool = False, previous_code: Optional[str] = None,
                                               model_engine: Optional[ModelEngine] = None,
                                               hidden_messages: GeneralMessageDesignation = None, **kwargs) -> str:
        return self.conversation_manager.get_and_append_assistant_message(
            tag=tag, comment=comment, is_code=is_code, previous_code=previous_code,
            model_engine=model_engine or self.model_engine,
            hidden_messages=hidden_messages, **kwargs)

    def apply_append_user_message(self, content: str, tag: Optional[str] = None, comment: Optional[str] = None,
                                  previous_code: Optional[str] = None):
        return self.conversation_manager.append_user_message(
            content=content, tag=tag, comment=comment, previous_code=previous_code)

    def apply_append_system_message(self, content: str, tag: Optional[str] = None, comment: Optional[str] = None):
        return self.conversation_manager.append_system_message(
            content=content, tag=tag, comment=comment)

    def apply_append_surrogate_message(self, content: str, tag: Optional[str] = None, comment: Optional[str] = None,
                                       previous_code: Optional[str] = None):
        return self.conversation_manager.append_surrogate_message(
            content=content, tag=tag, comment=comment, previous_code=previous_code)
