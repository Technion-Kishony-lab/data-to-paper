from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple, TypeVar, Type

from scientistgpt.conversation import Role, ConversationManager, GeneralMessageDesignation
from scientistgpt.utils.replacer import with_attribute_replacement
from scientistgpt.utils.text_utils import extract_text_between_tags, dedent_triple_quote_str

from .converser_gpt import ConverserGPT


_T = TypeVar("_T")


@dataclass
class DualConverserGPT(ConverserGPT):
    """
    A base class for agents running two chatgpts.
    """

    other_system_prompt: str = 'You are a helpful scientist.'

    other_conversation_name: str = None

    other_web_conversation_name: Optional[str] = None

    suppress_printing_other_conversation: bool = False

    @with_attribute_replacement
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

    @classmethod
    def from_converser(cls: Type[_T], converser: ConverserGPT, **kwargs) -> _T:
        """
        Create a new converser from an existing one.
        """
        if isinstance(converser, DualConverserGPT):
            dual_kwargs = {
                'other_conversation_name':
                    kwargs.pop('other_conversation_name', converser.other_conversation_name),
                'other_web_conversation_name':
                    kwargs.pop('other_web_conversation_name', converser.other_web_conversation_name),
            }
        else:
            dual_kwargs = {}
        return super().from_converser(
            converser=converser,
            **{**kwargs, **dual_kwargs},
        )

    @property
    def other_conversation(self):
        return self.other_conversation_manager.conversation

    @with_attribute_replacement
    def initialize_other_conversation_if_needed(self):
        self.other_conversation_manager.initialize_conversation_if_needed()
        if len(self.other_conversation) == 0:
            self.apply_to_other_append_system_message(self.other_system_prompt)
            # add the message also to the web conversation:
            self.apply_append_system_message(self.other_system_prompt, conversation_name=None, ignore=True,
                                             reverse_roles_for_web=True)

    def apply_to_other_get_and_append_assistant_message(self, tag: Optional[str] = None, comment: Optional[str] = None,
                                                        is_code: bool = False, previous_code: Optional[str] = None,
                                                        model_engine: Optional[str] = None,
                                                        hidden_messages: GeneralMessageDesignation = None, **kwargs,
                                                        ) -> str:
        return self.other_conversation_manager.get_and_append_assistant_message(
            tag=tag, comment=comment, is_code=is_code, previous_code=previous_code,
            model_engine=model_engine or self.model_engine,
            hidden_messages=hidden_messages, **kwargs)

    def apply_to_other_append_user_message(self, content: str, tag: Optional[str] = None, comment: Optional[str] = None,
                                           ignore: bool = False,
                                           previous_code: Optional[str] = None, is_background: bool = False):
        return self.other_conversation_manager.append_user_message(
            content, tag=tag, comment=comment, previous_code=previous_code,
            ignore=ignore, is_background=is_background)

    def apply_to_other_append_system_message(self, content: str, tag: Optional[str] = None,
                                             comment: Optional[str] = None):
        return self.other_conversation_manager.append_system_message(content, tag=tag, comment=comment)

    def apply_to_other_append_surrogate_message(self, content: str, tag: Optional[str] = None,
                                                comment: Optional[str] = None,
                                                ignore: bool = False,
                                                previous_code: Optional[str] = None,
                                                is_background: bool = False):
        return self.other_conversation_manager.append_surrogate_message(
            content, tag=tag, comment=comment, previous_code=previous_code,
            ignore=ignore, is_background=is_background)


class CycleStatus(Enum):
    FAILED_CHECK_SELF_RESPONSE = 'failed_check_self_response'
    NOT_APPROVED_BY_OTHER = 'not_approved_by_other'
    APPROVED_BY_OTHER = 'approved_by_other'
    MAX_ROUNDS_EXCEEDED = 'max_rounds_exceeded'


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

    sentence_to_add_to_error_message_upon_failed_check_self_response: str = ""
    fake_performer_message_to_add_after_max_rounds: str = \
        "No need for additional feedback. Thanks much - I think I have it now!"
    fake_performer_message_to_add_after_reviewer_approval: str = "Thanks much - this was very helpful!"
    max_reviewing_rounds: int = 3
    max_attempts_per_round: int = 4

    @with_attribute_replacement
    def __post_init__(self):
        super().__post_init__()
        # reverse roles:
        self.other_conversation_manager.assistant_agent = self.user_agent
        self.other_conversation_manager.user_agent = self.assistant_agent
        self.round_num = 0

    def get_response_from_other_in_response_to_response_from_self(self, altered_self_response: str) -> str:
        """
        Append response from self as user message to other conversation, and get response from other assistant.
        """
        self.round_num += 1
        self.apply_to_other_append_user_message(altered_self_response)
        return self.apply_to_other_get_and_append_assistant_message()

    def get_response_from_self_in_response_to_response_from_other(self, other_response: str) -> str:
        """
        Append response from other as user message to self conversation, and get response from assistant.
        """
        self.apply_append_user_message(self._alter_other_response(other_response))
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

    def is_completed(self) -> bool:
        """
        The dialog is completed when the other agent terminates the conversation, by responding with the
        termination phrase.
        """
        return len(self.other_conversation) > 1 and \
            self.termination_phrase.lower() in self.other_conversation.get_last_response().lower()

    @with_attribute_replacement
    def run_dialog(self, append_termination_response_to_self: bool = True) -> Optional[str]:
        """
        Run the dialog until it is completed.
        Returns the last chatgpt response from self.
        If we don't get a valid (by _check_self_response)self chatgpt response after max_attempts_per_round,
        return None.
        """
        last_self_response = None
        while True:
            self_response, cycle_status = self.run_one_cycle(append_termination_response_to_self)
            if cycle_status is CycleStatus.FAILED_CHECK_SELF_RESPONSE:
                return last_self_response
            if cycle_status is CycleStatus.MAX_ROUNDS_EXCEEDED:
                return self_response
            if cycle_status is CycleStatus.APPROVED_BY_OTHER:
                return self_response
            # cycle_status is CycleStatus.NOT_APPROVED_BY_OTHER
            last_self_response = self_response

    def _check_self_response(self, response: str) -> Optional[str]:
        """
        Check the response from self. If the response is not allowed, return a message to chatgpt describing
        the problem and requesting a new response.
        Otherwise, return None.
        """
        return None

    @with_attribute_replacement
    def run_one_cycle(self, append_termination_response_to_self: bool = True) -> Tuple[str, CycleStatus]:
        """
        Run one cycle of the dialog. Return str of response if completed, or None if not completed
        """
        self_response = None
        for _ in range(self.max_attempts_per_round):
            # to allow starting either before or after the first self response:
            is_preexisting_self_response = self.conversation.get_last_non_commenter_message().role is not Role.USER
            if is_preexisting_self_response:
                self_response = self.conversation.get_last_response()
            else:
                self_response = self.apply_get_and_append_assistant_message(web_conversation_name=None)
            problem_in_response = self._check_self_response(self_response)
            if problem_in_response is None:
                break
            if not is_preexisting_self_response:
                self.apply_append_surrogate_message(content=self_response, conversation_name=None)
            self.apply_append_user_message(problem_in_response + '\n' +
                                           self.sentence_to_add_to_error_message_upon_failed_check_self_response,
                                           tag='error')
        else:
            return self_response, CycleStatus.FAILED_CHECK_SELF_RESPONSE

        # We have a valid response from self. Now we can proceed with the dialog:
        if self.round_num >= self.max_reviewing_rounds:
            if not is_preexisting_self_response:
                self.apply_append_surrogate_message(content=self_response, conversation_name=None)
            if self.fake_performer_message_to_add_after_max_rounds is not None:
                self.apply_append_surrogate_message(self.fake_performer_message_to_add_after_max_rounds, ignore=True)
            return self_response, CycleStatus.MAX_ROUNDS_EXCEEDED

        altered_self_response = self._alter_self_response(self_response)
        if not is_preexisting_self_response:
            self.apply_append_surrogate_message(content=altered_self_response, conversation_name=None)
        other_response = self.get_response_from_other_in_response_to_response_from_self(altered_self_response)

        if self.is_completed():
            if append_termination_response_to_self:
                self.apply_append_user_message(other_response)
                if self.fake_performer_message_to_add_after_reviewer_approval:
                    self.apply_append_surrogate_message(self.fake_performer_message_to_add_after_reviewer_approval,
                                                        ignore=True)
            return self_response, CycleStatus.APPROVED_BY_OTHER

        self.get_response_from_self_in_response_to_response_from_other(other_response)
        return self_response, CycleStatus.NOT_APPROVED_BY_OTHER


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
        "{termination_phrase}" (termination-phase)
        If you feel that the initial {goal_noun} is already good enough, it is perfectly fine and encouraged \
        to respond with the termination-phrase immediately, without requesting any improvement cycles.
    """)

    sentence_to_add_at_the_end_of_reviewer_response: str = dedent_triple_quote_str("""
        Please correct your response according to my feedback and send back a complete rewrite of the {goal_noun}.
        Make sure to send the full corrected {goal_noun}, not just the parts that were revised.
        """)

    sentence_to_add_at_the_end_of_performer_response: str = None

    post_background_comment: str = 'Background messages completed. Requesting "{goal_noun}".'

    @property
    def are_we_reviewing_at_all(self) -> bool:
        return self.max_reviewing_rounds > 0

    def _alter_other_response(self, response: str) -> str:
        return response + '\n\n' + self.sentence_to_add_at_the_end_of_reviewer_response

    def _alter_self_response(self, response: str) -> str:
        if self.sentence_to_add_at_the_end_of_performer_response:
            return response + '\n\n' + self.sentence_to_add_at_the_end_of_performer_response
        else:
            return response

    def _pre_populate_background(self):
        """
        Add background messages to the two conversations to set them ready for the cycle.
        """
        pass

    def _pre_populate_conversations(self):
        """
        After system messages, we can add additional messages to the two conversation to set them ready for the cycle.
        """
        self._pre_populate_background()
        self.comment(self.post_background_comment, tag='after_background')
        self.apply_append_user_message(self.user_initiation_prompt, tag='user_initiation_prompt')

    @with_attribute_replacement
    def initialize_dialog(self):
        self.initialize_conversation_if_needed()
        if self.are_we_reviewing_at_all:
            self.initialize_other_conversation_if_needed()
        self._pre_populate_conversations()

    @with_attribute_replacement
    def initialize_and_run_dialog(self) -> str:
        self.initialize_dialog()
        return self.run_dialog()


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
        {quote_request}.
        """)

    def _extract_goal_from_response(self, response: str) -> str:
        for flanking_tags in self.flanking_tag_list:
            try:
                return extract_text_between_tags(response, *flanking_tags)
            except ValueError:
                pass
        raise ValueError(f'Could not find the {self.goal_noun} in the response.')

    def _check_self_response(self, response: str) -> Optional[str]:
        try:
            self._extract_goal_from_response(response)
        except ValueError:
            return self.quote_request
        return None

    @with_attribute_replacement
    def initialize_and_run_dialog(self):
        response = super().initialize_and_run_dialog()
        return self._extract_goal_from_response(response)
