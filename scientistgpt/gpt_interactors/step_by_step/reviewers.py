from dataclasses import dataclass, field
from typing import Optional, Dict, List, Union

from scientistgpt.cast import Agent
from scientistgpt.gpt_interactors.paper_writing.base_paper_writing import FailedCreatingPaperSection
from scientistgpt.gpt_interactors.step_by_step.base_scientific_conversers import BaseScientificReviewGPT
from scientistgpt.latex import extract_latex_section_from_response, FailedToExtractLatexContent
from scientistgpt.utils import dedent_triple_quote_str
from scientistgpt.utils.text_utils import nicely_join

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
    goal_noun: str = 'description and interpretation of the results'
    goal_verb: str = 'write'
    assistant_agent: Agent = Agent.PlanReviewer
    user_agent: Agent = Agent.Student
    sentence_to_add_at_the_end_of_reviewee_response: str = dedent_triple_quote_str("""
        Please provide feedback on the above {goal_noun}, with specific attention to whether this description \
        is fully supported by our data (pay specific attention to the output of our analysis code, above).
    """)


@dataclass
class BaseWriterReviewGPT(BaseScientificReviewGPT):
    """
    Base class for the writer of a paper section in latex format.
    """
    max_rounds: int = 3
    goal_noun: str = None
    conversation_name: str = None
    goal_verb: str = 'write'
    reviewee: str = 'scientific writer'
    reviewer: str = 'scientific reviewer'
    assistant_agent: Agent = Agent.Writer
    user_agent: Agent = Agent.Student
    section_names: Optional[Union[str, list[str]]] = None
    section_contents: Union[str, List[str]] = field(default_factory=list)

    def __post_init__(self):
        self.goal_noun = self.goal_noun or nicely_join(self.section_names)
        self.conversation_name = self.conversation_name or self.goal_noun.replace(' ', '_')
        super().__post_init__()

    system_prompt: str = dedent_triple_quote_str("""
        You are a scientist capable of writing full-length, scientifically sound research papers.

        You should:
        1. Write every part of the paper in scientific language, in `.tex` format.
        2. Write the paper section by section.
        3. Write the paper in a way that is consistent with the scientific products provided to you.
        4. Do not cite any papers.
        """)

    user_initiation_prompt: str = """
    Based on the material provided above (research goal, analysis plan, and results description), please {goal_verb} \
    only the {goal_noun} of a scientific paper. Do not write any other parts!
    Write in tex format including \\section{..}, any math or symbols that needs tex escapes.
    """

    other_system_prompt: str = """
    You are a {reviewer} for a {reviewee} who needs to {goal_verb} a {goal_noun} for a scientific paper.
    Your job is to advise me, the {reviewee}, and provide constructive bullet-point feedback in repeated cycles \
    of improvements and feedback.

    When you feel that the goal has been achieved, respond explicitly with: "{termination_phrase}" (termination-phase).
    """

    sentence_to_add_at_the_end_of_reviewer_response: str = """
    Please correct your response according to my feedback and send back a complete rewrite of the {goal_noun}.
    Make sure to send the full corrected {goal_noun}, not just the parts that were revised.
    """

    sentence_to_add_at_the_end_of_reviewee_response: str = \
        "Please provide constructive feedback on the above {goal_noun}"

    def _check_self_response(self, response: str, section_names=None) -> Optional[str]:
        """
        Check that the response is a valid latex section
        """
        try:
            self.section_contents = []
            for section_name in self.section_names:
                self.section_contents.append(extract_latex_section_from_response(response, section_name))
        except FailedToExtractLatexContent as e:
            error_message = dedent_triple_quote_str("""
                {}

                Please rewrite the {} part again with the correct latex formatting.
                """).format(e, self.goal_noun)
            return error_message
        return None

    def get_sections(self) -> Union[str, list[str]]:
        self.initialize_and_run_dialog()
        return self.section_contents


@dataclass
class TitleAbstractReviewGPT(BaseWriterReviewGPT):
    max_rounds: int = 2
    background_product_fields = ['data_file_descriptions', 'research_goal', 'analysis_plan', 'results_summary']


@dataclass
class PaperSectionReviewGPT(BaseWriterReviewGPT):
    max_rounds: int = 1
    background_product_fields = ['data_file_descriptions', 'research_goal', 'analysis_plan', 'results_summary',
                                 'title_and_abstract']
