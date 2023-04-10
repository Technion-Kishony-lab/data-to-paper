import re
from dataclasses import dataclass

from scientistgpt.utils.text_utils import dedent_triple_quote_str

from .converser_gpt import DialogConverserGPT, ConstructiveReviewDialogConverserGPT
from ..conversation.message_designation import RangeMessageDesignation


COMPLETION_PHRASE = 'I hereby approve the analysis plan'


def _is_answer_affirmative(answer: str) -> bool:
    return 'hereby approve' in answer.lower()


@dataclass
class ReviewerDialogConverserGPT(DialogConverserGPT):
    """
    Create a conversation between two chatgtps: the scientist and the reviewer.

    `conversation`: The conversation where the chatgpt is the scientist.
    `other_conversation`: The conversation where the chatgpt is the reviewer.
    """

    # override the default system prompt:
    other_system_prompt: str = 'You are a helpful scientific reviewer, whose aim is to provide constructive ' \
                               'feedback on a data analysis research plan.'

    # override the default conversation name:
    conversation_name: str = 'Scientist'
    other_conversation_name: str = 'PlanReviewer'

    max_review_cycles: int = 3

    def _set_conversation_with_reviewer(self):
        """
        Initialize the conversation with the reviewer.

        system: You are a helpful reviewer of a data analysis research plan.
        user: We have the following data files...
        assistant: Thank you for...
        user: Our goal is to...
        assistant: Thank you for...
        user: I will now provide my analysis plan. Please review it.
        assistant: Please specify your current research plan and I will review it.
        """
        self.initialize_other_conversation()
        self.other_conversation_manager.copy_messages_from_another_conversations(
            source_conversation=self.conversation,
            message_designation=RangeMessageDesignation.from_(start='data_description', end='ok_goal_description')
        )
        self.other_conversation_manager.append_user_message(dedent_triple_quote_str("""
        I will now provide my analysis plan. Please review it.
        If you are satisfied, please reply "{}".
        Otherwise, please provide a constructive bullet-point feedback.
        """).format(COMPLETION_PHRASE))
        self.other_conversation_manager.append_provided_assistant_message(dedent_triple_quote_str("""
        Please specify your current research plan and I will review it. 
        If the plan is satisfactory, I will reply with "{}". 
        Otherwise, I will provide a constructive feedback.
        """.format(COMPLETION_PHRASE)))

    def review_plan(self) -> str:
        """
        Review the analysis plan by creating a chatgpt-to-chatgpt conversation.
        """

        # We suppress print from the scientist conversation.
        # Otherwise, we will see each message twice, for each chatgpt.
        self.conversation_manager.should_print = False

        self._set_conversation_with_reviewer()

        num_review_cycle = 0
        while True:
            # get the revised plan response from the last scientist-chatgpt message:
            revised_plan = self.conversation.get_last_response()
            if num_review_cycle == self.max_review_cycles:
                break
            num_review_cycle += 1

            reviewer_tag = f'reviewer_comments_{num_review_cycle}'
            scientist_tag = f'revised_plan_{num_review_cycle}'

            # we provide the reviewer with the plan that we got from the scientist-chatgpt (as if it is the user plan):
            self.other_conversation_manager.append_user_message(
                revised_plan + "\n\n" +
                f'Please review the plan and provide feedback. \n'
                f'If you are satisfied with plan, please explicitly specify "{COMPLETION_PHRASE}".')
            reviewer_response = self.other_conversation_manager.get_and_append_assistant_message(tag=reviewer_tag)
            if _is_answer_affirmative(reviewer_response):
                break

            # we now provide the scientist-chatgpt with the reviewer's feedback (as if it is the user feedback):
            self.conversation_manager.append_user_message(
                reviewer_response + "\n\n" +
                "Please correct your plan according to my feedback and send me back the complete corrected plan "
                "(make sure to send the full corrected plan, not just the parts that were revised).",
                tag=reviewer_tag)
            self.conversation_manager.get_and_append_assistant_message(tag=scientist_tag)
        return revised_plan

