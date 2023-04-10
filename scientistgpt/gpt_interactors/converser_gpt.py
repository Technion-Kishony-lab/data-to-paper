from dataclasses import dataclass

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

    def initialize_conversation(self):
        self.conversation_manager.create_conversation()
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

    def initialize_other_conversation(self):
        self.other_conversation_manager.create_conversation()
        self.other_conversation_manager.append_system_message(self._other_system_prompt)


@dataclass
class RoleReversalDialogConverserGPT(DialogConverserGPT):
    """
    A base class for agents running a dialog between two chatgpts, where the roles of the two agents are reversed.
    """

    def get_next_response(self):
        """
        Get the next response from the other agent.
        """
        response = self.conversation_manager.get_and_append_assistant_message()
        self.other_conversation_manager.append_user_message(self._alter_response(response))

    def get_next_other_response(self):
        """
        Get the next response from the other agent.
        """
        other_response = self.other_conversation_manager.get_and_append_assistant_message()
        self.conversation_manager.append_user_message(self._alter_other_response(other_response))

    def _alter_response(self, response: str) -> str:
        """
        Alter the response from the agent.
        """
        return response

    def _alter_other_response(self, response: str) -> str:
        """
        Alter the response from the other agent.
        """
        return response

    def run_one_round_starting_with_self(self):
        """
        Run one round of the dialog.
        """
        self.get_next_response()
        self.get_next_other_response()

    def run_one_round_starting_with_other(self):
        """
        Run one round of the dialog.
        """
        self.get_next_other_response()
        self.get_next_response()


@dataclass
class ConstructiveReviewDialogConverserGPT(RoleReversalDialogConverserGPT):
    """
    A base class for agents running a dialog between two chatgpts one is a reviwee who needs to perform a task,
    and the other is a reviewer who provides constructive feedback.
    """

    reviewee: str = 'scientist'
    reviewer: str = 'scientific reviewer'

    system_prompt: str = \
        'You are a {reviewee} who needs to {goal_verb} {goal_noun}.\n' \
        'I will be your {reviewer}.'

    other_system_prompt: str = \
        'You are a {reviewer} for a {reviewee} who needs to {goal_verb} {goal_noun}.\n' \
        'Your job is to advise me, the {reviewee}, and provide constructive bullet-point feedback in repeated cycles ' \
        'of improvements and feedback.\n' \
        'When you feel that the goal has been achieved and you cannot advise of additional improvements, then ' \
        'respond with just two words: "Job completed".\n' \
        '\n' \
        'I will be the {reviewee} that you advise.'

    goal_noun: str = 'a one-paragraph summary on the solar system'
    """
    The goal of the reviewee. To fit the default formatting of the system prompts above, the goal should be specified 
    as a noun.
    """

    goal_verb: str = 'write'
    """
    The verb applied to the goal noun, like 'write', 'draw', 'build', 'code', etc.
    """

    max_rounds: int = 5

    def _replace_system_prompt(self, system_prompt):
        return system_prompt.format(reviewee=self.reviewee, reviewer=self.reviewer,
                                    goal_noun=self.goal_noun, goal_verb=self.goal_verb)

    @property
    def _system_prompt(self):
        return self._replace_system_prompt(self.system_prompt)

    @property
    def _other_system_prompt(self):
        return self._replace_system_prompt(self.other_system_prompt)

    def _alter_other_response(self, response: str) -> str:
        """
        Alter the response from the other agent.
        """
        return response + f'\n\nPlease correct your response and send back a complete rewrite of the {self.goal_noun}.'

    def initialize_dialog(self):
        self.initialize_conversation()
        self.initialize_other_conversation()
        self.conversation_manager.append_user_message(
            f'Hello {self.reviewee}. Please {self.goal_verb} {self.goal_noun}.')
        self.other_conversation_manager.should_print = False

    def is_completed(self):
        return len(self.other_conversation_manager.conversation) > 1 and \
            'job completed' in self.other_conversation_manager.conversation.get_last_response().lower()

    def run_dialog(self) -> str:
        for i in range(self.max_rounds):
            self.run_one_round_starting_with_self()
            if self.is_completed():
                return self.conversation_manager.conversation[-2].content
        raise RuntimeError('The conversation did not end with "Job completed"')


@dataclass
class CodeWritingGPT(ConverserGPT):
    """
    Interact with chatgpt to write a code that needs to create an output file.
    """

    output_filename = 'results.txt'
    """
    The name of the file that gpt code is instructed to save the results to.
    """

    gpt_script_filename = 'gpt_code'
    """
    The base name of the pythin file in which the code written by gpt is saved. 
    """


