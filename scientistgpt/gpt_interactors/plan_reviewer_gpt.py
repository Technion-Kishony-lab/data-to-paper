from dataclasses import dataclass

from scientistgpt.conversation.message_designation import RangeMessageDesignation
from scientistgpt.cast import Agent

from .dual_converser import ReviewDialogDualConverserGPT


@dataclass
class PlanReviewDialogDualConverserGPT(ReviewDialogDualConverserGPT):
    """
    Create a conversation between a scientist gpt and a reviewer gpt to review and improve the
    scientist's research plan.

    `conversation` (self): The conversation where the chatgpt is the scientist.
    `other_conversation` (other): The conversation where the chatgpt is the reviewer.
    """

    # roles and goal:
    reviewee: str = 'scientist'
    reviewer: str = 'scientific reviewer'
    goal_noun: str = 'a data analysis research plan'
    termination_phrase: str = 'I hereby approve the analysis plan'

    user_agent: Agent = Agent.Student
    assistant_agent: Agent = Agent.PlanReviewer

    # set conversation names:
    conversation_name: str = 'Scientist'
    other_conversation_name: str = 'PlanReviewer'

    def _pre_populate_conversations(self):
        """
        Initialize the conversation with the reviewer.
        """
        # ----- part added already in initialization -------------------------------
        # system: You are a helpful reviewer of a data analysis research plan.
        #
        # ----- part we now copy from scientist conversation -----------------------
        # user: We have the following data files...
        # assistant: Thank you for...
        # user: Our goal is to...
        # assistant: Thank you for...
        #
        # ----- new part we now add ------------------------------------------------
        # user: I will now provide my analysis plan. Please review it.
        # assistant: Please specify your current research plan and I will review it.

        self.other_conversation_manager.copy_messages_from_another_conversations(
            source_conversation=self.conversation,
            message_designation=RangeMessageDesignation.from_(start='data_description', end='ok_goal_description')
        )

        self.other_conversation_manager.append_user_message(self._format_prompt("""
        I will now provide my analysis plan. Please review it.
        If you are satisfied, please reply "{termination_phrase}".
        Otherwise, please provide a constructive bullet-point feedback.
        """))

        self.other_conversation_manager.append_surrogate_message(self._format_prompt("""
        Please specify your current research plan and I will review it. 
        If the plan is satisfactory, I will reply with "{termination_phrase}". 
        Otherwise, if the plan needs improvements. I will provide a constructive feedback 
        (and in this case will not use the phrase "{termination_phrase}"). 
        """))
