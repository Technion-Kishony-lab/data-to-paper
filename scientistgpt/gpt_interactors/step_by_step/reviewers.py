from dataclasses import dataclass

from scientistgpt.cast import Agent
from scientistgpt.gpt_interactors.step_by_step.base_scientific_conversers import BaseScientificReviewGPT
from scientistgpt.utils import dedent_triple_quote_str


sentence_to_add_at_the_end_of_reviewee_response = dedent_triple_quote_str("""\n
    Please provide feedback on the above {goal_noun}, with specific attention to whether it can be \
    studied using only the provided dataset, without requiring any additional data \
    (pay attention to using only data explicitly available in the provided headers of the our data files \
    as described in our dataset, above).
    Do not suggest changes to the {goal_noun} that may require data not available in our dataset.
    """)


@dataclass
class GoalReviewGPT(BaseScientificReviewGPT):
    background_product_fields = ['data_file_descriptions']
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
        
        Pay special attention to whether the research goal can be achieved using only the provided dataset (without \
        requiring additional data).

        When you feel that the provided research goal is interesting and can be achieved without requiring \
        additional data except the provided dataset, respond explicitly with: 
        "{termination_phrase}" (termination-phrase).
        If you feel that the initial goal description that I send you is already interesting, well defined, \
        and fits the provided data, it is perfectly fine and encouraged to respond with with termination-phrase \
        immediately, without requesting any improvement cycles.
        """
    sentence_to_add_at_the_end_of_reviewee_response: str = sentence_to_add_at_the_end_of_reviewee_response


@dataclass
class PlanReviewGPT(BaseScientificReviewGPT):
    max_rounds: int = 0  # no review cycles
    background_product_fields = ['data_file_descriptions', 'research_goal']
    conversation_name: str = 'analysis_plan'
    other_conversation_name: str = 'research_plan_reviewer'
    goal_noun: str = 'short data analysis plan'
    goal_verb: str = 'write'
    assistant_agent: Agent = Agent.PlanReviewer
    user_agent: Agent = Agent.Student
    sentence_to_add_at_the_end_of_reviewee_response: str = sentence_to_add_at_the_end_of_reviewee_response


@dataclass
class ResultsInterpretationReviewGPT(BaseScientificReviewGPT):
    max_rounds: int = 1
    background_product_fields = ['data_file_descriptions', 'research_goal', 'code_and_output']
    conversation_name: str = 'results_interpretation'
    other_conversation_name: str = 'results_interpretation_reviewer'
    goal_noun: str = 'description and interpretation of the results'
    goal_verb: str = 'write'
    assistant_agent: Agent = Agent.PlanReviewer
    user_agent: Agent = Agent.Student
    sentence_to_add_at_the_end_of_reviewee_response: str = dedent_triple_quote_str("""
        Please provide feedback on the above {goal_noun}, with specific attention to whether this description \
        is fully supported by our data (pay specific attention to the output of our analysis code, above).
    """)


@dataclass
class PaperSectionReviewGPT(BaseScientificReviewGPT):
    max_rounds: int = 1
    background_product_fields = ['data_file_descriptions', 'research_goal', 'analysis_plan', 'results_summary']
    conversation_name: str = 'results_interpretation'
    other_conversation_name: str = 'results_interpretation_reviewer'
    goal_noun: str = 'description and interpretation of the results'
    goal_verb: str = 'write'
    assistant_agent: Agent = Agent.PlanReviewer
    user_agent: Agent = Agent.Student
    sentence_to_add_at_the_end_of_reviewee_response: str = dedent_triple_quote_str("""
        Please provide feedback on the above {goal_noun}, with specific attention to whether this description \
        is fully supported by our data (pay specific attention to the output of our analysis code, above).
    """)
