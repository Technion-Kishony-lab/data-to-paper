from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, ClassVar

from scientistgpt.conversation.actions_and_conversations import ActionsAndConversations
from scientistgpt.env import COALESCE_WEB_CONVERSATIONS
from scientistgpt.conversation.conversation import WEB_CONVERSATION_NAME_PREFIX
from scientistgpt.conversation import ConversationManager, GeneralMessageDesignation
from scientistgpt.servers.openai_models import ModelEngine
from scientistgpt.utils.copier import Copier
from scientistgpt.utils.replacer import Replacer, with_attribute_replacement
from scientistgpt.utils.create_html import print_red
from scientistgpt.base_cast import Agent


@dataclass
class ConverserGPT(Replacer, Copier):
    """
    A base class for agents interacting with chatgpt.
    """
    COPY_ATTRIBUTES = {'actions_and_conversations', 'conversation_name', 'web_conversation_name', 'assistant_agent',
                       'user_agent'}
    ADDITIONAL_DICT_ATTRS = Replacer.ADDITIONAL_DICT_ATTRS | {'user_skin_name', 'assistant_skin_name'}

    actions_and_conversations: ActionsAndConversations = None

    model_engine: ClassVar[ModelEngine] = None
    """
    The openai model engine to use. If None, use the default model engine.
    A call to apply_get_and_append_assistant_message can override this value.
    """

    system_prompt: str = 'You are a helpful scientist.'

    assistant_agent: Agent = None
    user_agent: Agent = None

    conversation_name: str = 'default'

    web_conversation_name: Optional[str] = True
    # None - do not post to web conversation, True - use default name, str - use given name

    driver: str = ''

    @with_attribute_replacement
    def __post_init__(self):
        if self.web_conversation_name is True:
            # we determine an automatic conversation name based on the agent that the main agent is talking to:
            if COALESCE_WEB_CONVERSATIONS:
                web_conversation_name = \
                    self.user_agent.get_conversation_name() or self.assistant_agent.get_conversation_name()
            else:
                web_conversation_name = self.conversation_name
            if web_conversation_name:
                web_conversation_name = WEB_CONVERSATION_NAME_PREFIX + web_conversation_name
            self.web_conversation_name = web_conversation_name
        self.conversation_manager = ConversationManager(
            actions_and_conversations=self.actions_and_conversations,
            conversation_name=self.conversation_name,
            web_conversation_name=self.web_conversation_name,
            driver=self.driver if self.driver is not None else type(self).__name__,
            assistant_agent=self.assistant_agent,
            user_agent=self.user_agent,
        )

    @property
    def user_skin_name(self):
        return None if self.user_agent is None else self.user_agent.skin_name

    @property
    def assistant_skin_name(self):
        return None if self.assistant_agent is None else self.assistant_agent.skin_name

    @property
    def conversation(self):
        return self.conversation_manager.conversation

    @with_attribute_replacement
    def initialize_conversation_if_needed(self):
        self.conversation_manager.initialize_conversation_if_needed()
        if len(self.conversation) == 0 and self.system_prompt:
            self.apply_append_system_message(self.system_prompt)

    def comment(self, comment: str, tag: Optional[str] = None, as_action: bool = True, **kwargs):
        """
        Print a comment, either directly, or as an action appending a COMMENTER message to the conversation (default).
        """
        if as_action:
            self.conversation_manager.append_commenter_message(comment, tag=tag, **kwargs)
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
                                  ignore: bool = False, reverse_roles_for_web: bool = False,
                                  previous_code: Optional[str] = None, is_background: bool = False, **kwargs):
        return self.conversation_manager.append_user_message(
            content=content, tag=tag, comment=comment, ignore=ignore, reverse_roles_for_web=reverse_roles_for_web,
            previous_code=previous_code, is_background=is_background, **kwargs)

    def apply_append_system_message(self, content: str, tag: Optional[str] = None, comment: Optional[str] = None,
                                    ignore: bool = False, reverse_roles_for_web: bool = False,
                                    **kwargs):
        return self.conversation_manager.append_system_message(
            content=content, tag=tag, comment=comment, ignore=ignore,
            reverse_roles_for_web=reverse_roles_for_web, **kwargs)

    def apply_append_surrogate_message(self, content: str, tag: Optional[str] = None, comment: Optional[str] = None,
                                       ignore: bool = False, reverse_roles_for_web: bool = False,
                                       previous_code: Optional[str] = None, is_background: bool = False,
                                       **kwargs):
        return self.conversation_manager.append_surrogate_message(
            content=content, tag=tag, comment=comment, ignore=ignore, reverse_roles_for_web=reverse_roles_for_web,
            previous_code=previous_code, is_background=is_background, **kwargs)
