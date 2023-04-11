from dataclasses import dataclass
from typing import Optional

from scientistgpt import Role
from scientistgpt.conversation.converation_manager import ConversationManager


@dataclass
class ConverserGPT:
    """
    A base class for agents interacting with chatgpt.
    """

    system_prompt: str = 'You are a helpful scientist.'

    conversation_name: str = 'default'

    agent: str = ''

    def __post_init__(self):
        self.conversation_manager = ConversationManager(
            conversation_name=self.conversation_name,
            agent=self.agent
        )

    @property
    def _system_prompt(self):
        return self.system_prompt

    @property
    def conversation(self):
        return self.conversation_manager.conversation

    def initialize_conversation_if_needed(self):
        if self.conversation_manager.conversation is None:
            self.conversation_manager.create_conversation()
        if len(self.conversation) == 0:
            self.conversation_manager.append_system_message(self._system_prompt)


@dataclass
class DialogConverserGPT(ConverserGPT):
    """
    A base class for agents running a dialog between two chatgpts.
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
class RoleReversalDialogConverserGPT(DialogConverserGPT):
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

    max_rounds: int = 5

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
class ConstructiveReviewDialogConverserGPT(RoleReversalDialogConverserGPT):
    """
    A base class for agents running a dialog between two chatgpts, where one is a "reviwee" who needs to perform a task
    towards a certain "goal", and the other is a "reviewer" who provides constructive feedback.

    The interaction proceeds in repeated cycles of the reviwee performing the task and the reviewer providing feedback.
    """

    # Properties that should be set by each instance according to the task we want to perform:
    reviewee: str = 'scientist'
    reviewer: str = 'scientific reviewer'

    goal_noun: str = 'a one-paragraph summary on the solar system'
    """
    The goal of the reviewee. To fit the default formatting of the system prompts above, the goal should be specified 
    as a noun.
    """

    goal_verb: str = 'write'
    """
    The verb applied to the goal noun, like 'write', 'draw', 'build', 'code', etc.
    """

    # Properties that are more generic (can adjust if needed):
    system_prompt: str = \
        'You are a {reviewee} who needs to {goal_verb} {goal_noun}.\n' \
        'I will be your {reviewer}.'

    user_initiation_prompt: str = \
        'Hello {reviewee}. Please {goal_verb} {goal_noun}.'

    other_system_prompt: str = \
        'You are a {reviewer} for a {reviewee} who needs to {goal_verb} {goal_noun}.\n' \
        'Your job is to advise me, the {reviewee}, and provide constructive bullet-point feedback in repeated cycles ' \
        'of improvements and feedback.\n' \
        'When you feel that the goal has been achieved and you cannot advise of additional improvements, then ' \
        'respond explicitly with: "{termination_phrase}".\n' \
        '\n' \
        'I will be the {reviewee} that you advise.'

    sentence_to_add__at_the_end_of_reviewer_response: str = \
        'Please correct your response and send back a complete rewrite of the {goal_noun}.'

    def _format_prompt(self, system_prompt):
        return system_prompt.format(reviewee=self.reviewee, reviewer=self.reviewer,
                                    termination_phrase=self.termination_phrase,
                                    goal_noun=self.goal_noun, goal_verb=self.goal_verb)

    @property
    def _system_prompt(self):
        return self._format_prompt(self.system_prompt)

    @property
    def _other_system_prompt(self):
        return self._format_prompt(self.other_system_prompt)

    def _alter_other_response(self, response: str) -> str:
        return response + '\n\n' + self._format_prompt(self.sentence_to_add__at_the_end_of_reviewer_response)

    def _pre_populate_conversation(self):
        self.conversation_manager.append_user_message(self._format_prompt(self.user_initiation_prompt))

    def initialize_dialog(self, suppress_printing_of_other: bool = True):
        self.initialize_conversation_if_needed()
        self.initialize_other_conversation_if_needed()

        # Disable printing of the other_conversation because one is the same of the other (except for role reversal)
        if suppress_printing_of_other:
            self.other_conversation_manager.should_print = False
        self._pre_populate_conversation()


@dataclass
class CodeWritingGPT(ConverserGPT):
    """
    Interact with chatgpt to write a code that needs to create an output file.
    """

    output_filename: str = 'results.txt'
    """
    The name of the file that gpt code is instructed to save the results to.
    """

    gpt_script_filename: str = 'gpt_code'
    """
    The base name of the pythin file in which the code written by gpt is saved. 
    """
