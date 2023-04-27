from dataclasses import dataclass

from scientistgpt.cast import Agent
from scientistgpt.gpt_interactors.dual_converser import QuotedReviewDialogDualConverserGPT
from scientistgpt.gpt_interactors.text_extractors import TextExtractorGPT
from scientistgpt.gpt_interactors.types import ScientificProductsHolder, DataFileDescriptions
from scientistgpt.utils import dedent_triple_quote_str


@dataclass
class BaseScientificReviewGPT(QuotedReviewDialogDualConverserGPT, ScientificProductsHolder):
    suppress_printing_other_conversation: bool = True
    max_rounds: int = 1
    termination_phrase: str = 'I hereby approve the {goal_noun}'

    def _add_acknowledgement(self, previous_product: str, is_last: bool = True):
        thank_you_message = f"Thank you for {previous_product}. "
        self.apply_append_surrogate_message(thank_you_message)
        self.apply_to_other_append_surrogate_message(
            thank_you_message + (self._get_user_initiation_prompt() if is_last else ''))


@dataclass
class GoalReviewGPT(BaseScientificReviewGPT):
    conversation_name: str = 'research_goal'
    other_conversation_name: str = 'research_goal_reviewer'
    goal_noun: str = 'research goal'
    goal_verb: str = 'suggest'
    assistant_agent: Agent = Agent.PlanReviewer
    user_agent: Agent = Agent.Student
    termination_phrase: str = \
        'I hereby approve that the research goal is well-defined and can be studied using only the provided dataset'
    user_initiation_prompt: str = """
    Please {goal_verb} a {goal_noun}. Please do not include suggested methodology, just the research goal.
    Make sure you suggest a research goal that can be studied using only the provided dataset, without requiring \
    any additional data \
    (pay attention to using only data available based on the provided headers of the our data files \
    as in the description of our dataset, above).
    """
    other_system_prompt: str = """
        You are a {reviewer} for a {reviewee} who needs to {goal_verb} a {goal_noun}.
        Your job is to advise me, the {reviewee}, and provide a constructive bullet-point feedback in repeated cycles \
        of improvements and feedback.
        
        Pay special attention to whether the research goal can be studied using only the provided dataset (without \
        requiring additional data).

        When you feel that the provided research goal is interesting and can be studied without requiring \
        additional data except the provided dataset, respond explicitly with: 
        "{termination_phrase}" (termination-phrase).
        If you feel that the initial goal description that I send you is already interesting, well defined, \
        and fits the provided data, it is perfectly fine and encouraged to respond with the above \
        termination-phrase right at the beginning.
        """
    sentence_to_add_at_the_end_of_reviewee_response: str = dedent_triple_quote_str("""\n
        Please provide feedback on the above research goal, with specific attention to whether it can be \
        studied using only the provided dataset, without requiring additional data \
        (pay attention to using only data available based on the provided headers of the our data files \
        as in the description of our dataset, above).
        Do not suggest changes to the goal that may require data not available in our dataset.
        """)

    def _pre_populate_background(self, is_last: bool = True):
        self.apply_to_both_append_user_message(
            f"DESCRIPTION OF OUR DATASET.\n\n"
            f"We have the following {self.scientific_products.data_file_descriptions}")
        self._add_acknowledgement(previous_product='the dataset', is_last=is_last)


@dataclass
class PlanReviewGPT(GoalReviewGPT):
    conversation_name: str = 'research_plan'
    other_conversation_name: str = 'research_plan_reviewer'
    goal_noun: str = 'short data analysis plan'
    goal_verb: str = 'write'
    assistant_agent: Agent = Agent.PlanReviewer
    user_agent: Agent = Agent.Student

    def _pre_populate_background(self, is_last: bool = True):
        super()._pre_populate_background(is_last=False)  # add data description
        self.apply_to_both_append_user_message(f"DESCRIPTION OF OUR RESEARCH GOAL.\n\n"
                                               f"{self.scientific_products.research_goal}")
        self._add_acknowledgement(previous_product='the goal description', is_last=is_last)

    def _extract_plan_from_response(self, response: str) -> str:
        return TextExtractorGPT(
            assistant_agent=Agent.Secretary,
            user_agent=Agent.Student,
            text=response,
            description_of_text_to_extract='data analysis plan',
            max_number_of_attempts=3,
            conversation_name='extract_analysis_plan',
        ).extract_text(rewind_conversation=True)

    def initialize_and_run_dialog(self):
        response = super().initialize_and_run_dialog()
        return self._extract_plan_from_response(response)
