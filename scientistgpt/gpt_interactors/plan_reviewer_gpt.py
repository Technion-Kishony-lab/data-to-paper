import re
from dataclasses import dataclass
from typing import List, Optional


from scientistgpt.utils.text_utils import dedent_triple_quote_str, print_red
from scientistgpt.conversation import Conversation
from scientistgpt.proceed_retract import FuncAndRetractions

from .converser_gpt import ConverserGPT, DialogConverserGPT
from ..conversation.converation_manager import ConversationManager
from ..conversation.message_designation import RangeMessageDesignation


def word_count(text):
    """
    Count the number of words in provided test.
    """
    return len(re. findall(r'\w+', text))


REVIEWER_GPT_PROMPT = dedent_triple_quote_str("""
Is this {}plan satisfactory? (yes/no)
If yes, please reply in one word only, saying "yes".
If no, please give constructive feedback and specify how the plan could be improved.
""")


@dataclass
class PlanReviewerGPT(DialogConverserGPT):
    """
    Create a conversation between two chatgtps: the scientist and the reviewer.

    `conversation`: The conversation where the chatgpt is the reviewer.
    `other_conversation`: The conversation where the chatgpt is the scientist.
    """

    # override the default system prompt:
    system_prompt: str = 'You are a helpful reviewer of a data analysis research plan.'

    # override the default conversation name:
    conversation_name: str = 'PlanReviewerGPT'

    max_review_cycles: int = 3

    def _set_conversation_with_reviewer(self):
        """
        Initialize the conversation with the reviewer.

        system: You are a helpful reviewer of a data analysis research plan.
        user: We have the following data files...
        assistant: Thank you for...
        user: Our goal is to...
        assistant: Thank you for...
        user: [analysis_plan from chatgpt]
        """
        self.initialize_conversation()
        self.conversation_manager.copy_messages_from_another_conversations(
            source_conversation=self.other_conversation,
            message_designation=RangeMessageDesignation.from_(start='data_description', end='ok_goal_description')
        )

    def review_plan(self):
        """
        Review the analysis plan by creating a chatgpt-to-chatgpt conversation.

        cycles of:
            assistant: Thank you for the plan. Please specify what do you want me to do.
            user: Is plan satisfactory? (yes/no), If no, please give feedback.
            assistant: get chatgpt response -> <reviewer_comments>
        """

        for num_review_cycle in range(self.max_review_cycles):
            # we provide the plan that we got from chatgpt as our plan:
            self.conversation_manager.append_user_message(
                self.other_conversation.get_message_content_by_tag('analysis_plan'), tag='original_analysis_plan')
            self.conversation_manager.append_provided_assistant_message(
                'Thank you for the plan. Please specify what do you want me to do.')
            self.conversation.append_user_message(
                REVIEWER_GPT_PROMPT.format('' if num_review_cycle == 0 else 'improved '))
            reviewer_comments = self.conversation_manager.get_and_append_assistant_message(
                tag=f'reviewer_comments_{num_review_cycle}')
            if self.is_answer_affirmative(reviewer_comments):
                break
            else:
                self.other_conversation_manager.append_user_message(reviewer_comments)
                improved_plan = self.other_conversation_manager.get_and_append_assistant_message(
                    tag=f'improved_plan_{num_review_cycle}')
                self.conversation_manager.append_user_message(improved_plan, tag=f'improved_plan_{num_review_cycle}')

    @staticmethod
    def is_answer_affirmative(answer: str) -> bool:
        return 'yes' in answer.lower() and word_count(answer) <= 4

