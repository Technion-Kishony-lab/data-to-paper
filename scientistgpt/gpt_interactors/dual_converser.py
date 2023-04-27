from dataclasses import dataclass
from typing import Optional, Tuple, List

from scientistgpt.conversation import Role, ConversationManager

from .converser_gpt import ConverserGPT
from ..conversation.message_designation import GeneralMessageDesignation
from ..utils.text_utils import dedent_triple_quote_str, extract_text_between_tags


@dataclass
class DualConverserGPT(ConverserGPT):
    """
    A base class for agents running two chatgpts.
    """

    other_system_prompt: str = 'You are a helpful scientist.'

    other_conversation_name: str = 'other'

    suppress_printing_other_conversation: bool = False

    def __post_init__(self):
        super().__post_init__()
        self.other_conversation_manager = ConversationManager(
            conversation_name=self.other_conversation_name,
            driver=self.driver if self.driver is not None else type(self).__name__,
            should_print=not self.suppress_printing_other_conversation,
        )

    @property
    def actual_other_system_prompt(self):
        return self.other_system_prompt

    @property
    def other_conversation(self):
        return self.other_conversation_manager.conversation

    def initialize_other_conversation_if_needed(self):
        self.other_conversation_manager.initialize_conversation_if_needed()
        if len(self.other_conversation) == 0:
            self.apply_to_other_append_system_message(self.actual_other_system_prompt)

    def apply_to_other_get_and_append_assistant_message(self, tag: Optional[str] = None, comment: Optional[str] = None,
                                                        is_code: bool = False, previous_code: Optional[str] = None,
                                                        hidden_messages: GeneralMessageDesignation = None, **kwargs,
                                                     ) -> str:
        return self.other_conversation_manager.get_and_append_assistant_message(
            tag=tag, comment=comment, is_code=is_code, previous_code=previous_code,
            hidden_messages=hidden_messages, **kwargs)

    def apply_to_other_append_user_message(self, content: str, tag: Optional[str] = None, comment: Optional[str] = None,
                                           is_code: bool = False, previous_code: Optional[str] = None):
        return self.other_conversation_manager.append_user_message(
            content, tag=tag, comment=comment, is_code=is_code, previous_code=previous_code)

    def apply_to_other_append_system_message(self, content: str, tag: Optional[str] = None, comment: Optional[str] = None):
        return self.other_conversation_manager.append_system_message(content, tag=tag, comment=comment)

    def apply_to_other_append_surrogate_message(self, content: str, tag: Optional[str] = None,
                                                comment: Optional[str] = None,
                                                is_code: bool = False, previous_code: Optional[str] = None):
        return self.other_conversation_manager.append_surrogate_message(
            content, tag=tag, comment=comment, is_code=is_code, previous_code=previous_code)


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
    #                         can start        exceeds max_rounds
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
    """
    A phrase used by the 'other' chatgpt to terminate the conversation.
    """

    max_rounds: int = 3

    def __post_init__(self):
        super().__post_init__()
        # reverse roles:
        self.other_conversation_manager.assistant_agent = self.user_agent
        self.other_conversation_manager.user_agent = self.assistant_agent
        self.round_num = 0

    def get_response_from_other_in_response_to_response_from_self(self, self_response: str) -> str:
        """
        Append response from self as user message to other conversation, and get response from other assistant.
        """
        self.round_num += 1
        self.apply_to_other_append_user_message(self._alter_self_response(self_response))
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

    def run_dialog(self, append_termination_response_to_self: bool = True) -> str:
        """
        Run the dialog until it is completed.
        Returns the last chatgpt response from self.
        """
        while True:
            response = self.run_one_cycle(append_termination_response_to_self)
            if response is not None:
                return response

    def _check_self_response(self, response: str) -> Optional[str]:
        """
        Check the response from self. If the response is not allowed, return a description of the problem.
        Otherwise return None.
        """
        return None

    def run_one_cycle(self, append_termination_response_to_self: bool = True) -> Optional[str]:
        """
        Run one cycle of the dialog. Return str of response if completed, or None if not completed
        """

        while True:  # TODO: add a max number of tries
            # to allow starting either before or after the first self response:
            if self.conversation[-1].role is Role.USER:
                self_response = self.apply_get_and_append_assistant_message()
            else:
                self_response = self.conversation.get_last_response()
            problem_in_response = self._check_self_response(self_response)
            if problem_in_response is None:
                break
            self.apply_append_user_message(problem_in_response, tag='error')

        if self.round_num >= self.max_rounds:
            return self_response

        other_response = self.get_response_from_other_in_response_to_response_from_self(self_response)

        if self.is_completed():
            if append_termination_response_to_self:
                self.apply_append_user_message(other_response)
            return self_response

        self.get_response_from_self_in_response_to_response_from_other(other_response)


@dataclass
class ReviewDialogDualConverserGPT(DialogDualConverserGPT):
    """
    A base class for agents running a dialog between two chatgpts, where one is a "reviwee" who needs to perform a task
    towards a certain "goal", and the other is a "reviewer" who provides constructive feedback.

    The interaction proceeds in repeated cycles of the reviwee performing the task and the reviewer providing feedback.
    """

    # *** Properties that should be set according to the task we want to perform ***

    # roles:
    reviewee: str = 'scientist'
    reviewer: str = 'scientific reviewer'

    # goal_noun: the desired output of the conversation (expressed as a singular noun).
    goal_noun: str = 'one-paragraph summary on the solar system'

    # goal_verb: a verb applied to achieve the goal, like 'write', 'draw', 'build', 'code', etc.
    goal_verb: str = 'write'

    # *** Properties that are more generic (adjust only if needed) ***

    system_prompt: str = """
    You are a {reviewee} who needs to {goal_verb} a {goal_noun}.
    """

    user_initiation_prompt: str = """
    Please {goal_verb} a {goal_noun}.
    """

    other_system_prompt: str = """
    You are a {reviewer} for a {reviewee} who needs to {goal_verb} a {goal_noun}.
    Your job is to advise me, the {reviewee}, and provide constructive bullet-point feedback in repeated cycles \
    of improvements and feedback.

    When you feel that the goal has been achieved, respond explicitly with: "{termination_phrase}" (termination-phase).
    If you feel that the initial {goal_noun} is already good enough, it is perfectly fine and encouraged to respond \
    with the termination-phrase immediately, without requesting any improvement cycles.
    """

    sentence_to_add_at_the_end_of_reviewer_response: str = """
    Please correct your response according to my feedback and send back a complete rewrite of the {goal_noun}.
    Make sure to send the full corrected {goal_noun}, not just the parts that were revised.
    """

    sentence_to_add_at_the_end_of_reviewee_response: str = ""

    def _formatting_dict(self):
        return dict(reviewee=self.reviewee, reviewer=self.reviewer, termination_phrase=self.termination_phrase,
                    goal_noun=self.goal_noun, goal_verb=self.goal_verb)

    def _format_prompt(self, prompt):
        while True:
            old_prompt = prompt
            prompt = dedent_triple_quote_str(prompt.format(**self._formatting_dict()))
            if prompt == old_prompt:
                return prompt

    @property
    def actual_system_prompt(self):
        return self._format_prompt(self.system_prompt)

    @property
    def actual_other_system_prompt(self):
        return self._format_prompt(self.other_system_prompt)

    @property
    def are_we_reviewing_at_all(self) -> bool:
        return self.max_rounds > 0

    def _alter_other_response(self, response: str) -> str:
        return response + '\n\n' + self._format_prompt(self.sentence_to_add_at_the_end_of_reviewer_response)

    def _alter_self_response(self, response: str) -> str:
        return response + '\n\n' + self._format_prompt(self.sentence_to_add_at_the_end_of_reviewee_response)

    def _pre_populate_background(self):
        """
        Add background messages to the two conversations to set them ready for the cycle.
        """
        pass

    def _get_user_initiation_prompt(self):
        return self._format_prompt(self.user_initiation_prompt)

    def _pre_populate_conversations(self):
        """
        After system messages, we can add additional messages to the two conversation to set them ready for the cycle.
        """
        self._pre_populate_background()
        self.apply_append_user_message(self._get_user_initiation_prompt())

    def initialize_dialog(self):
        self.initialize_conversation_if_needed()
        if self.are_we_reviewing_at_all:
            self.initialize_other_conversation_if_needed()
        self._pre_populate_conversations()

    def initialize_and_run_dialog(self) -> str:
        self.initialize_dialog()
        return self.run_dialog()


@dataclass
class QuotedReviewDialogDualConverserGPT(ReviewDialogDualConverserGPT):
    """
    A base class for agents running a dialog between two chatgpts, where one is a "reviwee" who needs to perform a task
    towards a certain "goal", and the other is a "reviewer" who provides constructive feedback.
    The reviewee is expected to return the goal as a triple-quoted string, so that it can be extracted.
    """

    flanking_tag_list = [('```', '```'), ('"""', '"""'), ("'''", "'''"), ('`', '`'), ('"', '"'), ("'", "'")]
    quote_request = 'Please return the {goal_noun} enclosed within triple-backticks.'

    sentence_to_add_at_the_end_of_reviewer_response: str = """
    Please correct your response according to my feedback and send back a complete rewrite of the {goal_noun}.
    {quote_request}.
    """

    def _formatting_dict(self):
        return {**super()._formatting_dict(), 'quote_request': self.quote_request}

    def _extract_goal_from_response(self, response: str) -> str:
        for flanking_tags in self.flanking_tag_list:
            try:
                return extract_text_between_tags(response, *flanking_tags)
            except ValueError:
                pass
        raise ValueError(f'Could not find the {self.goal_noun} in the response.')

    def _get_user_initiation_prompt(self):
        s = super()._get_user_initiation_prompt()
        s += self._format_prompt('\n\n' + self.quote_request)
        return s

    def _check_self_response(self, response: str) -> Optional[str]:
        try:
            self._extract_goal_from_response(response)
        except ValueError:
            return self._format_prompt(self.sentence_to_add_at_the_end_of_reviewee_response)
        return None

    def initialize_and_run_dialog(self):
        response = super().initialize_and_run_dialog()
        return self._extract_goal_from_response(response)
