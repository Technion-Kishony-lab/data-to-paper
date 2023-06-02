from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Tuple, Any

from scientistgpt.conversation import Role, ConversationManager, GeneralMessageDesignation, Message
from scientistgpt.utils.text_extractors import extract_text_between_tags
from scientistgpt.utils import dedent_triple_quote_str
from scientistgpt.utils.replacer import StrOrTextFormat, format_value

from .converser_gpt import ConverserGPT
from .exceptions import FailedCreatingProductException


class CycleStatus(Enum):
    FAILED_CHECK_SELF_RESPONSE = 'failed_check_self_response'
    NOT_APPROVED_BY_OTHER = 'not_approved_by_other'
    APPROVED_BY_OTHER = 'approved_by_other'
    MAX_ROUNDS_EXCEEDED = 'max_rounds_exceeded'


class NoResponse:
    pass


@dataclass
class SelfResponseError(Exception):
    """
    Exception raised when the response to a request for a latex section is not acceptable.
    """
    error_message: StrOrTextFormat = None

    def __str__(self):
        return self.error_message


@dataclass
class DualConverserGPT(ConverserGPT):
    """
    A base class for agents running two chatgpts.
    """
    COPY_ATTRIBUTES = ConverserGPT.COPY_ATTRIBUTES | {'other_conversation_name', 'other_web_conversation_name'}

    other_system_prompt: str = 'You are a helpful scientist.'

    other_conversation_name: str = None

    other_web_conversation_name: Optional[str] = None

    suppress_printing_other_conversation: bool = False

    def __post_init__(self):
        super().__post_init__()
        if self.other_conversation_name is None:
            self.other_conversation_name = f'{self.conversation_name}_other'
        self.other_conversation_manager = ConversationManager(
            actions_and_conversations=self.actions_and_conversations,
            conversation_name=self.other_conversation_name,
            web_conversation_name=self.other_web_conversation_name,
            driver=self.driver if self.driver is not None else type(self).__name__,
            should_print=not self.suppress_printing_other_conversation,
        )

    @property
    def other_conversation(self):
        return self.other_conversation_manager.conversation

    def _pre_populate_other_background(self):
        """
        Add background messages to the other conversation.
        Only called if we are starting a new conversation.
        """
        pass

    def initialize_other_conversation_if_needed(self):
        self.other_conversation_manager.initialize_conversation_if_needed()
        if len(self.other_conversation) == 0:
            self.apply_to_other_append_system_message(self.other_system_prompt)
            # add the message also to the web conversation:
            self.apply_append_system_message(self.other_system_prompt, conversation_name=None, ignore=True,
                                             reverse_roles_for_web=True)
            self._pre_populate_other_background()

    def apply_to_other_get_and_append_assistant_message(self, tag: Optional[StrOrTextFormat] = None,
                                                        comment: Optional[StrOrTextFormat] = None,
                                                        is_code: bool = False, previous_code: Optional[str] = None,
                                                        model_engine: Optional[str] = None,
                                                        hidden_messages: GeneralMessageDesignation = None,
                                                        expected_tokens_in_response: int = None,
                                                        should_format: bool = True, **kwargs) -> Message:
        return self.other_conversation_manager.get_and_append_assistant_message(
            tag=format_value(self, tag, should_format),
            comment=comment,
            is_code=is_code, previous_code=previous_code,
            model_engine=model_engine or self.model_engine,
            expected_tokens_in_response=expected_tokens_in_response,
            hidden_messages=hidden_messages, **kwargs)

    def apply_to_other_append_user_message(self, content: StrOrTextFormat, tag: Optional[StrOrTextFormat] = None,
                                           comment: Optional[StrOrTextFormat] = None,
                                           ignore: bool = False,
                                           previous_code: Optional[str] = None, is_background: bool = False,
                                           should_format: bool = True, **kwargs) -> Message:
        return self.other_conversation_manager.append_user_message(
            content=format_value(self, content, should_format),
            tag=tag,
            comment=comment,
            previous_code=previous_code,
            ignore=ignore, is_background=is_background, **kwargs)

    def apply_to_other_append_system_message(self, content: StrOrTextFormat, tag: Optional[StrOrTextFormat] = None,
                                             comment: Optional[StrOrTextFormat] = None,
                                             should_format: bool = True, **kwargs) -> Message:
        return self.other_conversation_manager.append_system_message(
            content=format_value(self, content, should_format),
            tag=tag,
            comment=comment,
            **kwargs)

    def apply_to_other_append_surrogate_message(self, content: StrOrTextFormat,
                                                tag: Optional[StrOrTextFormat] = None,
                                                comment: Optional[StrOrTextFormat] = None,
                                                ignore: bool = False,
                                                previous_code: Optional[str] = None,
                                                is_background: bool = False,
                                                should_format: bool = True, **kwargs) -> Message:
        return self.other_conversation_manager.append_surrogate_message(
            content=format_value(self, content, should_format),
            tag=tag,
            comment=comment,
            previous_code=previous_code,
            ignore=ignore, is_background=is_background, **kwargs)


@dataclass
class DialogDualConverserGPT(DualConverserGPT):
    """
    A base class for agents running a dialog between two chatgpts (self and other), where the roles of the two
    agents are reversed. The ASSISTANT response from one conversation is used as the USER response in the other
    conversation, and vice versa.

    A conversation is formed between the two agents. The conversation is terminated when the other agent
    terminates the conversation by issuing a termination_phrase, or when a maximum number of rounds has been reached.

    The conversation can start with self either after its first response or before.
    """

    #                                               end if
    #                         can start             exceeds max_reviewing_rounds
    #                           here                  ^
    #                            |                    |
    #                            v               self_response
    #      end if             SELF.chatgpt  -------------------->  OTHER.user
    # termination_phrase   <---  |                                     |
    # in other_response       SELF.user     <--------------------  OTHER.chatgpt
    #                           ^                other_response
    #                           |                round_num += 1
    #                         or, can
    #                         start here

    termination_phrase: str = 'Job completed'
    "A phrase used by the 'other' chatgpt to terminate the conversation."

    append_termination_response_to_self: bool = True

    sentence_to_add_to_error_message_upon_failed_check_self_response: str = ""
    fake_performer_message_to_add_after_max_rounds: str = \
        "No need for additional feedback. Thanks much - I think I have it now!"
    fake_performer_message_to_add_after_reviewer_approval: str = "Thanks much - this was very helpful!"
    max_reviewing_rounds: int = 3

    max_attempts_per_round: int = 4

    # Output:
    returned_value: Any = field(default_factory=NoResponse)

    def __post_init__(self):
        super().__post_init__()
        # reverse roles:
        self.other_conversation_manager.assistant_agent = self.user_agent
        self.other_conversation_manager.user_agent = self.assistant_agent
        self.round_num = 0

    def get_response_from_other_in_response_to_response_from_self(self, altered_self_response: str) -> Message:
        """
        Append response from self as user message to other conversation, and get response from other assistant.
        """
        self.round_num += 1
        self.apply_to_other_append_user_message(altered_self_response)
        return self.apply_to_other_get_and_append_assistant_message()

    def get_response_from_self_in_response_to_response_from_other(self, altered_other_response: str) -> Message:
        """
        Append response from other as user message to self conversation, and get response from assistant.
        """
        self.apply_append_user_message(altered_other_response)
        return self.apply_get_and_append_assistant_message()

    def _alter_self_response(self, response: str) -> str:
        """
        Alter the response from self.
        """
        return response

    def _alter_other_response(self, response: str) -> str:
        """
        Alter the response from other.
        """
        return response

    def _is_reviewer_response_terminating(self, reviewer_response: str, termination_phrase: str) -> bool:
        """
        Check if the response from the reviewer terminates the conversation.
        """
        return termination_phrase.lower() in reviewer_response.lower()

    def is_completed(self) -> bool:
        """
        The dialog is completed when the other agent terminates the conversation, by responding with the
        termination phrase.
        """
        if len(self.other_conversation) <= 1:
            return False
        reviewer_response = self.other_conversation.get_last_response()
        termination_phrase = format_value(self, self.termination_phrase)
        return self._is_reviewer_response_terminating(reviewer_response, termination_phrase)

    def run_dialog(self) -> CycleStatus:
        """
        Run the dialog until it is completed.
        Returns the reason for termination.
        """
        while True:
            cycle_status = self.run_one_cycle()
            if cycle_status is not CycleStatus.NOT_APPROVED_BY_OTHER:
                return cycle_status

    def _raise_self_response_error(self, error_message: str):
        """
        Raise a SelfResponseError with the given error message.
        """
        raise SelfResponseError(error_message)

    def _check_and_extract_value_from_self_response(self, response: str):
        """
        Check the response from self.
        Extract any needed information into returned_value.
        If the there are errors that require self to revise the response, raise an SelfResponseError describing
        the problem and requesting a new response.
        """
        return None

    def run_one_cycle(self) -> CycleStatus:
        """
        Run one cycle of the dialog. Makes updates to returned_value by calling
        _check_and_extract_value_from_self_response().
        """
        self_message = None
        for _ in range(self.max_attempts_per_round):
            # to allow starting either before or after the first self response:
            is_preexisting_self_response = self.conversation.get_last_non_commenter_message().role is not Role.USER
            if is_preexisting_self_response:
                self_response = self.conversation.get_last_response()
            else:
                self_message = self.apply_get_and_append_assistant_message(web_conversation_name=None)
                self_response = self_message.content
            try:
                self._check_and_extract_value_from_self_response(self_response)
                break
            except SelfResponseError as e:
                if not is_preexisting_self_response:
                    self.apply_append_surrogate_message(content=self_response, conversation_name=None,
                                                        context=self_message.context)
                self.apply_append_user_message(format_value(self, e.error_message) + '\n' +
                                               self.sentence_to_add_to_error_message_upon_failed_check_self_response,
                                               tag='error')
        else:
            return CycleStatus.FAILED_CHECK_SELF_RESPONSE

        # We have a valid response from self. Now we can proceed with the dialog:
        if self.round_num >= self.max_reviewing_rounds:
            if not is_preexisting_self_response:
                self.apply_append_surrogate_message(content=self_response, conversation_name=None,
                                                    context=self_message.context)
            if self.fake_performer_message_to_add_after_max_rounds is not None:
                self.apply_append_surrogate_message(self.fake_performer_message_to_add_after_max_rounds, ignore=True)
            return CycleStatus.MAX_ROUNDS_EXCEEDED

        altered_self_response = self._alter_self_response(self_response)
        if not is_preexisting_self_response:
            self.apply_append_surrogate_message(content=altered_self_response, conversation_name=None,
                                                context=self_message.context)
        other_message = self.get_response_from_other_in_response_to_response_from_self(altered_self_response)
        other_response = other_message.content
        altered_other_response = self._alter_other_response(other_response)
        if self.is_completed():
            if self.append_termination_response_to_self:
                self.apply_append_user_message(other_response, context=other_message.context)
                if self.fake_performer_message_to_add_after_reviewer_approval:
                    self.apply_append_surrogate_message(self.fake_performer_message_to_add_after_reviewer_approval,
                                                        ignore=True)
            return CycleStatus.APPROVED_BY_OTHER

        self.get_response_from_self_in_response_to_response_from_other(altered_other_response)
        return CycleStatus.NOT_APPROVED_BY_OTHER


@dataclass
class ReviewDialogDualConverserGPT(DialogDualConverserGPT):
    """
    A base class for agents running a dialog between two chatgpts, where one is a "reviwee" who needs to perform a task
    towards a certain "goal", and the other is a "reviewer" who provides constructive feedback.

    The interaction proceeds in repeated cycles of the reviwee performing the task and the reviewer providing feedback.
    """

    # *** Properties that should be set according to the task we want to perform ***

    # roles:
    performer: str = 'scientist'
    reviewer: str = 'scientific reviewer'

    # goal_noun: the desired output of the conversation (expressed as a singular noun).
    goal_noun: str = 'one-paragraph summary on the solar system'

    # goal_verb: a verb applied to achieve the goal, like 'write', 'draw', 'build', 'code', etc.
    goal_verb: str = 'write'

    # *** Properties that are more generic (adjust only if needed) ***

    system_prompt: str = "You are a {performer} who needs to {goal_verb} a {goal_noun}."

    user_initiation_prompt: str = "Please {goal_verb} a {goal_noun}."

    other_system_prompt: str = dedent_triple_quote_str("""
        You are a {reviewer} for a {performer} who needs to {goal_verb} a {goal_noun}.
        Your job is to advise me, the {performer}, and provide constructive bullet-point feedback in repeated cycles \
        of improvements and feedback.

        When you feel that the goal has been achieved, respond explicitly with: 
        "{termination_phrase}" (approving-phrase)
        If you feel that the initial {goal_noun} is already good enough, it is perfectly fine and encouraged \
        to respond with the approving-phrase immediately, without requesting any improvement cycles.
    """)

    sentence_to_add_at_the_end_of_reviewer_response: str = dedent_triple_quote_str("""
        Please correct your response according to my feedback and send back a complete rewrite of the {goal_noun}.
        Make sure to send the full corrected {goal_noun}, not just the parts that were revised.
        """)

    sentence_to_add_at_the_end_of_performer_response: str = None

    @property
    def are_we_reviewing_at_all(self) -> bool:
        return self.max_reviewing_rounds > 0

    def _alter_other_response(self, response: str) -> str:
        return response + '\n' + self.sentence_to_add_at_the_end_of_reviewer_response

    def _alter_self_response(self, response: str) -> str:
        if self.sentence_to_add_at_the_end_of_performer_response:
            return response + '\n' + self.sentence_to_add_at_the_end_of_performer_response
        else:
            return response

    def _pre_populate_background(self):
        """
        Add background messages to the two conversations to set them ready for the cycle.
        """
        self.apply_append_user_message(self.user_initiation_prompt, tag='user_initiation_prompt')

    def initialize_dialog(self):
        self.initialize_conversation_if_needed()
        if self.are_we_reviewing_at_all:
            self.initialize_other_conversation_if_needed()

    def initialize_and_run_dialog(self) -> CycleStatus:
        self.initialize_dialog()
        return self.run_dialog()

    def get_value_and_termination_reason(self) -> Tuple[Any, CycleStatus]:
        termination_reason = self.initialize_and_run_dialog()
        if isinstance(self.returned_value, NoResponse):
            raise FailedCreatingProductException()
        return self.returned_value, termination_reason

    def get_value(self):
        return self.get_value_and_termination_reason()[0]


@dataclass
class QuotedReviewDialogDualConverserGPT(ReviewDialogDualConverserGPT):
    """
    A base class for agents running a dialog between two chatgpts, where one is a "reviwee" who needs to perform a task
    towards a certain "goal", and the other is a "reviewer" who provides constructive feedback.
    The performer is expected to return the goal as a triple-quoted string, so that it can be extracted.
    """

    flanking_tag_list = [('```', '```'), ('"""', '"""'), ("'''", "'''")]
    quote_request: str = 'Please return the {goal_noun} enclosed within triple-backticks (but send text, not code).'
    user_initiation_prompt: str = ReviewDialogDualConverserGPT.user_initiation_prompt + '\n{quote_request}'

    sentence_to_add_at_the_end_of_reviewer_response: str = dedent_triple_quote_str("""
        Please correct your response according to my feedback and send back a complete rewrite of the {goal_noun}.
        {quote_request}
        """)

    def _check_and_extract_value_from_self_response(self, response: str):
        for flanking_tags in self.flanking_tag_list:
            try:
                self.returned_value = extract_text_between_tags(response, *flanking_tags)
                break
            except ValueError:
                pass
        else:
            self._raise_self_response_error(self.quote_request)
