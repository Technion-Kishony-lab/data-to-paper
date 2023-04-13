from dataclasses import dataclass
from typing import Optional

from scientistgpt.conversation import Role, ConversationManager

from .converser_gpt import ConverserGPT
from ..utils.text_utils import dedent_triple_quote_str


@dataclass
class DualConverserGPT(ConverserGPT):
    """
    A base class for agents running two chatgpts.
    """

    other_system_prompt: str = 'You are a helpful scientist.'

    other_conversation_name: str = 'other'

    def __post_init__(self):
        super().__post_init__()
        self.other_conversation_manager = ConversationManager(
            conversation_name=self.other_conversation_name,
            agent=self.agent
        )

    @property
    def _other_system_prompt(self):
        return self.other_system_prompt

    @property
    def other_conversation(self):
        return self.other_conversation_manager.conversation

    def initialize_other_conversation_if_needed(self):
        if self.other_conversation_manager.conversation is None:
            self.other_conversation_manager.create_conversation()
        if len(self.other_conversation) == 0:
            self.other_conversation_manager.append_system_message(self._other_system_prompt)


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
        self.round_num = 0

    def get_response_from_other_in_response_to_response_from_self(self, self_response: str) -> str:
        """
        Append response from self as user message to other conversation, and get response from other assistant.
        """
        self.round_num += 1
        self.other_conversation_manager.append_user_message(self._alter_self_response(self_response))
        return self.other_conversation_manager.get_and_append_assistant_message()

    def get_response_from_self_in_response_to_response_from_other(self, other_response: str) -> str:
        """
        Append response from other as user message to self conversation, and get response from assistant.
        """
        self.conversation_manager.append_user_message(self._alter_other_response(other_response))
        return self.conversation_manager.get_and_append_assistant_message()

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
        return len(self.other_conversation_manager.conversation) > 1 and \
            self.termination_phrase.lower() in self.other_conversation_manager.conversation.get_last_response().lower()

    def run_dialog(self, append_termination_response_to_self: bool = True) -> str:
        """
        Run the dialog until it is completed.
        Returns the last chatgpt response from self.
        """
        while True:
            response = self.run_one_cycle(append_termination_response_to_self)
            if response is not None:
                return response

    def run_one_cycle(self, append_termination_response_to_self: bool = True) -> Optional[str]:
        """
        Run one cycle of the dialog. Return str of response if completed, or None if not completed
        """

        # to allow starting either before or after the first self response:
        if self.conversation[-1].role is Role.USER:
            self_response = self.conversation_manager.get_and_append_assistant_message()
        else:
            self_response = self.conversation.get_last_response()

        if self.round_num >= self.max_rounds:
            return self_response

        other_response = self.get_response_from_other_in_response_to_response_from_self(self_response)

        if self.is_completed():
            if append_termination_response_to_self:
                self.conversation_manager.append_user_message(other_response)
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
    I will be your {reviewer}.
    """

    user_initiation_prompt: str = """
    Hello {reviewee}. Please {goal_verb} a {goal_noun}.
    """

    other_system_prompt: str = """
    You are a {reviewer} for a {reviewee} who needs to {goal_verb} a {goal_noun}.
    Your job is to advise me, the {reviewee}, and provide constructive bullet-point feedback in repeated cycles
    of improvements and feedback.

    When you feel that the goal has been achieved and you cannot advise of additional improvements, then
    respond explicitly with: "{termination_phrase}".
    """

    sentence_to_add_at_the_end_of_reviewer_response: str = """
    Please correct your response according to my feedback and send back a complete rewrite of the {goal_noun}.
    Make sure to send the full corrected {goal_noun}, not just the parts that were revised.
    """

    def _format_prompt(self, prompt):
        return dedent_triple_quote_str(prompt.format(
            reviewee=self.reviewee, reviewer=self.reviewer, termination_phrase=self.termination_phrase,
            goal_noun=self.goal_noun, goal_verb=self.goal_verb))

    @property
    def _system_prompt(self):
        return self._format_prompt(self.system_prompt)

    @property
    def _other_system_prompt(self):
        return self._format_prompt(self.other_system_prompt)

    def _alter_other_response(self, response: str) -> str:
        return response + '\n\n' + self._format_prompt(self.sentence_to_add_at_the_end_of_reviewer_response)

    def _pre_populate_conversations(self):
        """
        After system messages, we can add additional messages to the two conversation to set them ready for the cycle.
        """
        self.conversation_manager.append_user_message(self._format_prompt(self.user_initiation_prompt))

    def initialize_dialog(self, suppress_printing_of_other: bool = True):
        self.initialize_conversation_if_needed()
        self.initialize_other_conversation_if_needed()

        # Disable printing of the other_conversation because one is the same of the other (except for role reversal)
        if suppress_printing_of_other:
            self.other_conversation_manager.should_print = False
        self._pre_populate_conversations()

    def initialize_and_run_dialog(self, suppress_printing_of_other: bool = True):
        self.initialize_dialog(suppress_printing_of_other)
        return self.run_dialog()
