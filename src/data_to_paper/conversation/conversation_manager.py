from dataclasses import dataclass
from typing import Optional, Set, Iterable, Union, List

from data_to_paper.utils.print_to_file import print_and_log_red
from data_to_paper.base_cast import Agent
from data_to_paper.servers.llm_call import try_get_llm_response
from data_to_paper.servers.model_engine import OPENAI_CALL_PARAMETERS_NAMES, OpenaiCallParameters, ModelEngine
from data_to_paper.run_gpt_code.code_utils import add_label_to_first_triple_quotes_if_missing

from .actions_and_conversations import ActionsAndConversations, Conversations, Actions
from .conversation import Conversation
from .message import Message, Role, create_message, create_message_from_other_message
from .message_designation import GeneralMessageDesignation, convert_general_message_designation_to_list
from .conversation_actions import ConversationAction, AppendMessage, DeleteMessages, ResetToTag, \
    AppendLLMResponse, FailedLLMResponse, ReplaceLastMessage, \
    CreateConversation, AddParticipantsToConversation


@dataclass
class ConversationManager:
    """
    Manages an LLM conversation.
    Maintains a complete record of actions performed on the conversation.

    Allows processing Actions that act on the conversation.
    Maintains a list of these actions.
    """

    actions_and_conversations: ActionsAndConversations

    should_print: bool = True
    "Indicates whether to print added actions to the console."

    conversation_name: Optional[str] = None

    driver: str = ''
    "Name of the algorithm that is instructing this conversation manager."

    assistant_agent: Agent = None
    "The agent who is playing the assistant in the conversation."

    user_agent: Agent = None
    "The agent who is playing the user in the conversation."

    human_agent: Agent = None

    @property
    def conversations(self) -> Conversations:
        return self.actions_and_conversations.conversations

    @property
    def actions(self) -> Actions:
        return self.actions_and_conversations.actions

    @property
    def conversation(self) -> Conversation:
        return self.conversations.get_conversation(self.conversation_name)

    @property
    def participants(self) -> Set[Agent]:
        return {self.assistant_agent, self.user_agent}

    def _apply_action(self, action: ConversationAction):
        """
        Apply an action to a conversation and append to the actions list.
        """
        self.actions.apply_action(action, is_color=True)

    def _create_and_apply_action(self, action_type: type, **kwargs):
        """
        Create and apply an action to a conversation and append to the actions list.
        """
        self._apply_action(action_type(
            should_print=self.should_print,
            conversations=self.conversations,
            conversation_name=kwargs.pop('conversation_name', self.conversation_name),
            driver=kwargs.pop('driver', self.driver),
            **kwargs))

    def create_conversation(self):
        self._create_and_apply_action(CreateConversation, participants=self.participants)

    def add_participants(self, agents: Iterable[Agent]):
        self._create_and_apply_action(AddParticipantsToConversation, participants=set(agents))

    def initialize_conversation_if_needed(self):
        if self.conversation is None:
            self.create_conversation()
        else:
            if self.participants - self.conversation.participants:
                self.add_participants(self.participants - self.conversation.participants)

    def append_message(self, message: Message, comment: Optional[str] = None, **kwargs):
        """
        Append a message to a specified conversation.
        """
        self._create_and_apply_action(AppendMessage, message=message, comment=comment, **kwargs)

    def create_and_append_message(self, role: Role, content: str, tag: Optional[str], comment: Optional[str] = None,
                                  ignore: bool = False, previous_code: Optional[str] = None, is_code: bool = False,
                                  context: Optional[List[Message]] = None,
                                  is_background: bool = False, **kwargs):
        """
        Append a message to a specified conversation.
        """
        if role in [Role.ASSISTANT, Role.SURROGATE, Role.SYSTEM]:
            agent = self.assistant_agent
        elif role == Role.USER:
            agent = self.user_agent
        else:
            agent = None
        message = create_message(role=role, content=content, tag=tag, agent=agent, ignore=ignore,
                                 context=context, previous_code=previous_code, is_code=is_code,
                                 is_background=is_background)
        self.append_message(message, comment, **kwargs)

    def append_system_message(self, content: str, tag: Optional[str] = None, comment: Optional[str] = None,
                              ignore: bool = False,
                              is_background: bool = None, **kwargs):
        """
        Append a system-message to a specified conversation.
        """
        tag = tag or 'system_prompt'
        self.create_and_append_message(Role.SYSTEM, content, tag, comment,
                                       ignore=ignore, is_background=is_background,
                                       **kwargs)

    def append_user_message(self, content: str, tag: Optional[str] = None, comment: Optional[str] = None,
                            ignore: bool = False,
                            previous_code: Optional[str] = None, is_background: bool = False, **kwargs):
        """
        Append a user-message to a specified conversation.
        """
        self.create_and_append_message(Role.USER, content, tag, comment,
                                       ignore=ignore, previous_code=previous_code, is_background=is_background,
                                       **kwargs)

    def append_commenter_message(self, content: str, tag: Optional[str] = None,
                                 comment: Optional[str] = None, **kwargs):
        """
        Append a commenter-message to a specified conversation.

        Commenter messages are messages that are not sent to the LLM,
        rather they are just used as comments to the chat.
        """
        self.create_and_append_message(Role.COMMENTER, content, tag, comment, **kwargs)

    def append_surrogate_message(self, content: str, tag: Optional[str] = None, comment: Optional[str] = None,
                                 ignore: bool = False,
                                 previous_code: Optional[str] = None,
                                 is_background: bool = False, **kwargs):
        """
        Append a message with a pre-determined assistant content to a conversation (as if it came from the LLM).
        """
        self.create_and_append_message(Role.SURROGATE, content, tag, comment,
                                       ignore=ignore, previous_code=previous_code, is_background=is_background,
                                       **kwargs)

    def get_and_append_assistant_message(self, tag: Optional[str] = None, comment: Optional[str] = None,
                                         is_code: bool = False, previous_code: Optional[str] = None,
                                         is_json: bool = False,
                                         hidden_messages: GeneralMessageDesignation = None,
                                         expected_tokens_in_response: int = None,
                                         **kwargs  # for both create_message and openai params
                                         ) -> Message:
        """
        Get and append a response from openai to a specified conversation.

        If failed, retry while removing more messages upstream.
        """
        hidden_messages = convert_general_message_designation_to_list(hidden_messages)
        indices_and_messages = self.conversation.get_chosen_indices_and_messages(hidden_messages)
        actual_hidden_messages = hidden_messages.copy()

        # extract all OPENAI_CALL_PARAMETERS_NAMES from kwargs:
        openai_call_parameters = \
            OpenaiCallParameters(**{k: kwargs.pop(k) for k in OPENAI_CALL_PARAMETERS_NAMES if k in kwargs})

        # we try to get a response. if we fail we bump the model, and then gradually remove messages from the top,
        # starting at message 1 (we don't remove message 0, which is the system message).
        model = openai_call_parameters.model_engine or ModelEngine.DEFAULT
        while True:
            message = self._try_get_and_append_llm_response(tag=tag, comment=comment, is_code=is_code,
                                                            is_json=is_json,
                                                            previous_code=previous_code,
                                                            hidden_messages=actual_hidden_messages,
                                                            openai_call_parameters=openai_call_parameters,
                                                            expected_tokens_in_response=expected_tokens_in_response,
                                                            **kwargs)
            if isinstance(message, Message):
                return message

            # we failed to get a response. We start by bumping the model, if possible:
            try:
                model = model.get_model_with_more_context()
                model_was_bumped = True
            except ValueError:
                model_was_bumped = False
            if model_was_bumped:
                print_and_log_red(f'############# Bumping model #############')
                openai_call_parameters.model_engine = model
                continue

            # We have no option but to remove messages from the top:
            if len(indices_and_messages) <= 1:
                # we tried removing all messages and failed.
                raise RuntimeError('Failed accessing openai despite removing all messages from context.')
            print_and_log_red(f'############# Removing message from context #############')
            index, _ = indices_and_messages.pop(1)
            actual_hidden_messages.append(index)

    def _try_get_and_append_llm_response(self, tag: Optional[str], comment: Optional[str] = None,
                                         is_code: bool = False, previous_code: Optional[str] = None,
                                         is_json: bool = False,
                                         hidden_messages: GeneralMessageDesignation = None,
                                         openai_call_parameters: Optional[OpenaiCallParameters] = None,
                                         expected_tokens_in_response: int = None,
                                         **kwargs
                                         ) -> Union[Message, Exception]:
        """
        Try to get and append a response from openai to a specified conversation.

        The conversation is sent to openai after removing the messages with indices listed in hidden_messages.

        If getting a response is successful then append to the conversation, record action and return response string.
        If failed due to openai exception. Record a failed action and return the exception.
        """
        openai_call_parameters = openai_call_parameters or OpenaiCallParameters()
        if is_json:
            openai_call_parameters.response_format = {"type": "json_object"}
        messages = self.conversation.get_chosen_messages(hidden_messages)
        content = try_get_llm_response(messages, expected_tokens_in_response=expected_tokens_in_response,
                                       **openai_call_parameters.to_dict())
        if isinstance(content, Exception):
            self._create_and_apply_action(
                FailedLLMResponse, comment=comment, hidden_messages=hidden_messages, exception=content)
            return content

        if is_code:
            content = add_label_to_first_triple_quotes_if_missing(content, 'python')
        message = create_message(
            context=messages,
            role=Role.ASSISTANT, content=content, tag=tag, agent=self.assistant_agent,
            openai_call_parameters=None if openai_call_parameters.is_all_none() else openai_call_parameters,
            previous_code=previous_code, is_code=is_code,
            is_json=is_json)
        self._create_and_apply_action(
            AppendLLMResponse, comment=comment, hidden_messages=hidden_messages, message=message, **kwargs)
        return message

    def reset_back_to_tag(self, tag: str, comment: Optional[str] = None):
        """
        Reset the conversation to the last message with the specified tag.
        All messages following the message with the specified tag will be deleted.
        The message with the specified tag will be kept.
        """
        self._create_and_apply_action(ResetToTag, comment=comment, tag=tag)

    def delete_messages(self, message_designation: GeneralMessageDesignation, comment: Optional[str] = None):
        """
        Delete messages from a conversation.
        """
        self._create_and_apply_action(DeleteMessages, comment=comment, message_designation=message_designation)

    def replace_last_message(self, content: str, agent: Optional[Agent] = None, comment: Optional[str] = None
                             ) -> Message:
        """
        Replace the last message with the specified content.
        """
        message = create_message_from_other_message(
            other_message=self.conversation[-1], content=content, agent=agent)
        self._create_and_apply_action(ReplaceLastMessage, comment=comment, message=message)
        return message
