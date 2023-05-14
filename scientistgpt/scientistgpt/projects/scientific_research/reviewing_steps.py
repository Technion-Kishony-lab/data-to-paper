from dataclasses import dataclass
from typing import Optional, Union

from scientistgpt.utils import dedent_triple_quote_str
from scientistgpt.utils.replacer import with_attribute_replacement
from scientistgpt.utils.text_utils import nicely_join
from scientistgpt.servers.openai_models import ModelEngine
from scientistgpt.base_steps import BaseProductsQuotedReviewGPT, BaseLatexProductsReviewGPT

from .cast import ScientificAgent


@dataclass
class ScientificProductsQuotedReviewGPT(BaseProductsQuotedReviewGPT):

    sentence_to_add_at_the_end_of_performer_response: str = dedent_triple_quote_str("""
        Please provide feedback on the above {goal_noun}, with specific attention to whether it can be \
        studied using only the provided dataset, without requiring any additional data \
        (pay attention to using only data explicitly available in the provided headers of the our data files \
        as described in our dataset, above).
        Do not suggest changes to the {goal_noun} that may require data not available in our dataset.
        If you are satisfied, respond with "{termination_phrase}".
        """)


@dataclass
class GoalReviewGPT(ScientificProductsQuotedReviewGPT):
    max_reviewing_rounds: int = 1
    background_product_fields = ['data_file_descriptions']
    conversation_name: str = 'research_goal'
    other_conversation_name: str = 'research_goal_reviewer'
    goal_noun: str = 'research goal'
    goal_verb: str = 'suggest'
    assistant_agent: ScientificAgent = ScientificAgent.Performer
    user_agent: ScientificAgent = ScientificAgent.GoalReviewer
    termination_phrase: str = \
        'I hereby approve the research goal'
    user_initiation_prompt: str = dedent_triple_quote_str("""
        Please {goal_verb} a {goal_noun}. Please do not include suggested methodology, just the research goal.
        Make sure you suggest a research goal that can be studied using only the provided dataset, without requiring \
        any additional data \
        (pay attention to using only data available based on the provided headers of the our data files \
        as in the description of our dataset, above).

        {quote_request}
        """)
    other_system_prompt: str = dedent_triple_quote_str("""
        You are a {reviewer} for a {performer} who needs to {goal_verb} a {goal_noun}.
        Your job is to advise me, the {performer}, and provide a constructive bullet-point feedback in repeated cycles \
        of improvements and feedback.

        Pay special attention to whether the research goal can be achieved using only the provided dataset (without \
        requiring additional data).

        When you feel that the provided research goal is interesting and can be achieved without requiring \
        additional data except the provided dataset, respond explicitly with: 
        "{termination_phrase}" (termination-phrase).
        If you feel that the initial goal description that I send you is already interesting, well defined, \
        and fits the provided data, it is perfectly fine and encouraged to respond with with termination-phrase \
        immediately, without requesting any improvement cycles.
        """)


@dataclass
class PlanReviewGPT(ScientificProductsQuotedReviewGPT):
    max_reviewing_rounds: int = 0  # no review cycles
    fake_performer_message_to_add_after_max_rounds: str = 'No need for feedback. Thanks much!'
    background_product_fields = ['data_file_descriptions', 'research_goal']
    conversation_name: str = 'analysis_plan'
    goal_noun: str = 'short data analysis plan'
    goal_verb: str = 'write'
    assistant_agent: ScientificAgent = ScientificAgent.Performer
    user_agent: ScientificAgent = ScientificAgent.PlanReviewer


@dataclass
class ResultsInterpretationReviewGPT(ScientificProductsQuotedReviewGPT):
    max_reviewing_rounds: int = 1
    background_product_fields = ['data_file_descriptions', 'research_goal', 'code_and_output']
    conversation_name: str = 'results_interpretation'
    goal_noun: str = '"description and interpretation" of data analysis results'
    goal_verb: str = 'write'
    assistant_agent: ScientificAgent = ScientificAgent.Performer
    user_agent: ScientificAgent = ScientificAgent.InterpretationReviewer
    model_engine = ModelEngine.GPT4
    sentence_to_add_at_the_end_of_performer_response: str = dedent_triple_quote_str("""
        Please provide feedback on the above {goal_noun}, with specific attention to whether this description \
        is fully supported by our data (pay specific attention to the output of our analysis code, above).

        If you are satisfied, respond with "{termination_phrase}".
    """)
    user_initiation_prompt: str = "Please {goal_verb} a {goal_noun}. " + \
                                  "Briefly mention the tools used to preform the analysis.\n\n" \
                                  "{quote_request}"


@dataclass
class BaseWriterReviewGPT(BaseLatexProductsReviewGPT):
    """
    Base class for the writer of a paper section in latex format.
    """
    fake_performer_request_for_help: str = 'Hi {user_skin_name}, could you please help me {goal_verb} ' \
                                           'the "{goal_noun}" section for my paper?'

    max_reviewing_rounds: int = 3
    goal_noun: str = None
    conversation_name: str = None
    goal_verb: str = 'write'
    performer: str = 'scientific writer'
    reviewer: str = 'scientific reviewer'
    assistant_agent: ScientificAgent = ScientificAgent.Performer
    user_agent: ScientificAgent = ScientificAgent.Writer
    section_names: Optional[Union[str, list[str]]] = None

    def __post_init__(self):
        self.goal_noun = self.goal_noun or nicely_join(self.section_names)
        self.conversation_name = self.conversation_name or self.goal_noun.replace(' ', '_')
        super().__post_init__()

    system_prompt: str = dedent_triple_quote_str("""
        You are a data-scientist with experience writing accurate scientific research papers.

        You should:
        1. Write every section of the paper in scientific language, in `.tex` format.
        2. Write the paper section by section.
        3. Write the paper in a way that is fully consistent with the scientific products we have.
        4. Write the text without adding any citations (we will only add citations in a later stage).
        """)

    user_initiation_prompt: str = dedent_triple_quote_str("""
        Based on the material provided above (research goal, analysis plan, and results description), \
        please {goal_verb} only the "{goal_noun}" section of a scientific paper. Do not write any other parts!
        Write in tex format including the proper latex commands, any math or symbols that needs tex escapes.
        """)

    termination_phrase: str = 'I hereby approve the paper section'

    other_system_prompt: str = dedent_triple_quote_str("""
        You are a reviewer for a scientist who is writing a scientific paper about their data analysis results.
        Your job is to provide constructive bullet-point feedback in repeated cycles \
        of improvements and feedback.
        We will write each section of the research paper separately. 
        When you feel that the paper section i well-written and accurate, respond explicitly with:
         "{termination_phrase}".
        If you feel that my initial writing is already good enough, it is perfectly fine \
        to respond immediately with the above phrase ("{termination_phrase}"), \
        without requesting any improvement cycles.
    """)

    sentence_to_add_at_the_end_of_reviewer_response: str = dedent_triple_quote_str("""
        Please correct your response according to my feedback and send back a complete rewrite of the {goal_noun}.
        Make sure to send the full corrected {goal_noun}, not just the parts that were revised.
    """)

    sentence_to_add_at_the_end_of_performer_response: str = dedent_triple_quote_str("""
        Please provide constructive feedback on the above "{goal_noun}" for my paper.
        If you are satisfied, respond with "{termination_phrase}".
        """)


@dataclass
class TitleAbstractReviewGPT(BaseWriterReviewGPT):
    max_reviewing_rounds: int = 2
    background_product_fields = ['data_file_descriptions', 'research_goal', 'analysis_plan', 'results_summary']
    user_initiation_prompt: str = dedent_triple_quote_str("""
        Based on the material provided above (research goal, analysis plan, and results description), \
        please {goal_verb} only the "{goal_noun}" of a scientific paper. Do not write any other parts at this stage!
        Write in tex format including the \\\\title{{}} and \\\\begin{{abstract}} ... \\\\end{{abstract}} commands, \
        and any math or symbols that needs tex escapes.
    """)


@dataclass
class PaperSectionReviewGPT(BaseWriterReviewGPT):
    section_name: str = None
    max_reviewing_rounds: int = 1
    background_product_fields = ['data_file_descriptions', 'research_goal', 'analysis_plan', 'results_summary',
                                 'title_and_abstract']
    user_initiation_prompt: str = dedent_triple_quote_str("""
        Based on the material provided above (research goal, analysis plan, results description, and \
        the paper title and abstract), \
        please {goal_verb} only the "{goal_noun}" section of a scientific paper. Do not write any other parts!
        Write in tex format including the \\\\section{{}} command, and any math or symbols that needs tex escapes.
    """)

    def __post_init__(self):
        self.section_names = [self.section_name]
        super().__post_init__()

    @with_attribute_replacement
    def get_section(self):
        return self.get_sections()[0]


@dataclass
class PaperSectionWithTablesReviewGPT(PaperSectionReviewGPT):
    goal_noun: str = '{section_name} section with tables'
    goal_verb: str = 'rewrite'
    user_agent: ScientificAgent = ScientificAgent.TableExpert
    background_product_fields = ['results_summary', 'code_and_output', 'title_and_abstract']
    max_reviewing_rounds: int = 0
    user_initiation_prompt: str = dedent_triple_quote_str("""
        Based on the material provided above (research goal, results description, and outputs), please {goal_verb} \
        only the "{goal_noun}".
        Usually in scientific papers include one or two tables summarizing the main findings.
        The tables should include information that was only extracted from the information provided.
        Add the tables centered in booktabs, multirow format with caption and label. 
        In addition, change the results section text to refer to the tables (use their labels if necessary),
        to incorporate them as integral part of the {section_name} section. Do not add figures, only tables.
        Write in tex format including \\\\section{{}} command, any math or symbols that needs tex escapes.
    """)

    def _get_background_product_fields(self):
        return self.background_product_fields + ['most_updated_paper_sections_' + self.section_name]
