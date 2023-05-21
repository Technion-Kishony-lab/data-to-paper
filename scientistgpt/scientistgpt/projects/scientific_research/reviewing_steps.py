from dataclasses import dataclass
from typing import Tuple, Dict, Any, Optional

from scientistgpt.utils import dedent_triple_quote_str
from scientistgpt.utils.nice_list import nicely_join
from scientistgpt.base_steps import BaseProductsQuotedReviewGPT, BaseLatexProductsReviewGPT, \
    BasePythonValueProductsReviewGPT

from .cast import ScientificAgent
from ...latex import extract_latex_section_from_response


@dataclass
class ScientificProductsQuotedReviewGPT(BaseProductsQuotedReviewGPT):

    sentence_to_add_at_the_end_of_performer_response: str = dedent_triple_quote_str("""
        Please provide feedback on the above {goal_noun}, with specific attention to whether it can be \
        studied using only the provided dataset, without requiring any additional data \
        (pay attention to using only data explicitly available in the provided headers of our data files \
        as described in our dataset, above).
        Do not suggest changes to the {goal_noun} that may require data not available in our dataset.
        If you are satisfied, respond with "{termination_phrase}".
        """)


@dataclass
class GoalReviewGPT(ScientificProductsQuotedReviewGPT):
    max_reviewing_rounds: int = 1
    background_product_fields = ('data_file_descriptions', 'data_exploration_code_and_output')
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
        and fits the provided data, you can respond with with termination-phrase \
        immediately, without requesting any improvement cycles.
        """)


@dataclass
class PlanReviewGPT(ScientificProductsQuotedReviewGPT):
    max_reviewing_rounds: int = 1  # no review cycles
    fake_performer_message_to_add_after_max_rounds: str = 'No need for feedback. Thanks much!'
    background_product_fields = ('data_file_descriptions', 'data_exploration_code_and_output', 'research_goal')
    conversation_name: str = 'analysis_plan'
    goal_noun: str = 'short data analysis plan'
    user_initiation_prompt: str = dedent_triple_quote_str("""
        Please {goal_verb} a {goal_noun}. 
        Do not include any data visualization steps.
        Explicitly specify all relevant analysis results and values that should be calculated.
        {quote_request}
        """)
    goal_verb: str = 'write'
    assistant_agent: ScientificAgent = ScientificAgent.Performer
    user_agent: ScientificAgent = ScientificAgent.PlanReviewer


@dataclass
class TablesReviewGPT(BasePythonValueProductsReviewGPT):
    max_reviewing_rounds: int = 1
    background_product_fields = ('data_file_descriptions', 'data_exploration_code_and_output', 'research_goal')
    conversation_name: str = 'tables'
    value_type: type = Dict[str, str]
    goal_noun: str = 'two to three tables for a scientific paper'
    goal_verb: str = 'produce'
    assistant_agent: ScientificAgent = ScientificAgent.Performer
    user_agent: ScientificAgent = ScientificAgent.TableExpert
    sentence_to_add_at_the_end_of_performer_response: str = dedent_triple_quote_str("""
        Please provide feedback on the above tables, with specific attention to whether the tables \
        contain only information that is explicitly extracted from the results data. Compare the numbers in the tables \
        to the numbers in the results data and explicitly mention any discrepancies that need to get fixed.
        Do not suggest changes to the {goal_noun} that may require data not available in our dataset.
        If you are satisfied, respond with "{termination_phrase}".
        """)
    user_initiation_prompt: str = dedent_triple_quote_str("""
        Please {goal_verb} {goal_noun} that summarize the results we got in the output.
        The {goal_noun} should only include information that is explicitly extracted from the results data.
        The tables should be centered, in booktabs, multirow format with caption and label. 
        Make sure that the tables are not too wide, so that they fit text width.
        The tables should be returned in a dictionary, where the keys are the table titles, and the values are the \
        latex code for the tables.
        like this:
        {
            'Table 1: My first table': '\\begin{{table}} ... \\end{{table}}',
            'Table 2: My second table': '\\begin{{table}} ... \\end{{table}}',
        }
        {quote_request}
        """)

    def _check_response_value(self, response_value: Any) -> Optional[str]:
        for table_name, table_content in response_value.items():
            extract_latex_section_from_response(table_content, 'table')
        return None


@dataclass
class KeyNumericalResultsExtractorReviewGPT(BasePythonValueProductsReviewGPT):
    max_reviewing_rounds: int = 1
    background_product_fields = ('data_file_descriptions', 'data_exploration_code_and_output', 'research_goal')
    conversation_name: str = 'key_numerical_results_extractor'
    value_type: type = Dict[str, str]
    goal_noun: str = 'key numerical results'
    goal_verb: str = 'extract'
    assistant_agent: ScientificAgent = ScientificAgent.Performer
    user_agent: ScientificAgent = ScientificAgent.InterpretationReviewer
    sentence_to_add_at_the_end_of_performer_response: str = dedent_triple_quote_str("""
        Please provide feedback on the above {goal_noun}, with specific attention to whether the {goal_noun} \
        contain only information that is explicitly extracted from the results data. Compare the numbers in the \
        {goal_noun} to the numbers in the results data and explicitly mention any discrepancies that need to get fixed.

        If you are satisfied, respond with "{termination_phrase}".
        """)
    user_initiation_prompt: str = dedent_triple_quote_str("""
        Please {goal_verb} {goal_noun} that {goal_verb} the essence of the results we got in the output.
        The {goal_noun} you choose should be those that are cannot be presented in tables but are essential to the \
        resulted paper. 
        The {goal_noun} should only include information that is explicitly extracted from the results data.
        The {goal_noun} should be returned in a dictionary, where the keys are the names of the numerical results, \
        and the values are the actual numeric values themselves.
        like this:
        {
            'accuracy of logistic regression': 0.835,
            'AUC ROC of logistic regression': 0.77,
        }
        Obviously, this is just an example. You should choose the {goal_noun} that are relevant to the specific \
        results we got in the output.
        {quote_request}
        """)


@dataclass
class ResultsInterpretationReviewGPT(ScientificProductsQuotedReviewGPT):
    max_reviewing_rounds: int = 1
    background_product_fields = ('data_file_descriptions', 'research_goal', 'data_analysis_code_and_output')
    conversation_name: str = 'results_interpretation'
    goal_noun: str = '"description and interpretation" of data analysis results'
    goal_verb: str = 'write'
    assistant_agent: ScientificAgent = ScientificAgent.Performer
    user_agent: ScientificAgent = ScientificAgent.InterpretationReviewer
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
    fake_performer_request_for_help: str = \
        'Hi {user_skin_name}, could you please help me {goal_verb} the {pretty_section_names} for my paper?'

    max_reviewing_rounds: int = 3
    goal_noun: str = '{pretty_section_names} section of the paper'
    conversation_name: str = None
    goal_verb: str = 'write'
    performer: str = 'scientific writer'
    reviewer: str = 'scientific reviewer'
    assistant_agent: ScientificAgent = ScientificAgent.Performer
    user_agent: ScientificAgent = ScientificAgent.Writer

    def __post_init__(self):
        self.conversation_name = self.conversation_name or nicely_join(self.section_names, separator='_')
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
        Based on the material provided above ({actual_background_product_names}), \
        please {goal_verb} only the {pretty_section_names} of a scientific paper.
        Do not write any other parts!
        {latex_instructions}
        """)

    latex_instructions: str = ''

    termination_phrase: str = 'I hereby approve the paper section'

    other_system_prompt: str = dedent_triple_quote_str("""
        You are a reviewer for a scientist who is writing a scientific paper about their data analysis results.
        Your job is to provide constructive bullet-point feedback in repeated cycles \
        of improvements and feedback.
        We will write each section of the research paper separately. 
        When you feel that the paper section is well-written and accurate, you should explicitly say:
         "{termination_phrase}".
        If you feel that my initial writing is already good enough, it is perfectly fine \
        to respond immediately with the above phrase ("{termination_phrase}"), \
        without requesting any improvement cycles.
    """)

    sentence_to_add_at_the_end_of_reviewer_response: str = dedent_triple_quote_str("""
        Please correct your response according to my feedback and send back a complete rewrite \
        of the {pretty_section_names}.
        Make sure to send the full corrected {pretty_section_names}, not just the parts that were revised.
    """)

    sentence_to_add_at_the_end_of_performer_response: str = dedent_triple_quote_str("""
        Please provide constructive feedback on the above {pretty_section_names} for my paper.
        If you are satisfied, respond with "{termination_phrase}".
        """)


@dataclass
class TitleAbstractReviewGPT(BaseWriterReviewGPT):
    max_reviewing_rounds: int = 2
    background_product_fields = ('data_file_descriptions', 'research_goal', 'analysis_plan', 'results_summary')
    latex_instructions: str = dedent_triple_quote_str("""
        Write in tex format including the \\title{} and \\begin{abstract} ... \\end{abstract} commands, \
        and any math or symbols that needs tex escapes.
        """)


@dataclass
class PaperSectionReviewGPT(BaseWriterReviewGPT):
    max_reviewing_rounds: int = 1
    background_product_fields = ('data_file_descriptions', 'research_goal', 'analysis_plan', 'results_summary',
                                 'title_and_abstract')
    latex_instructions: str = dedent_triple_quote_str("""
        Write in tex format including the \\section{} command, \
        and any math or symbols that needs tex escapes.
        """)


@dataclass
class PaperSectionReferringTablesReviewGPT(PaperSectionReviewGPT):
    goal_verb: str = 'refer to tables in'
    user_agent: ScientificAgent = ScientificAgent.TableExpert
    background_product_fields = ('title_and_abstract', 'numerical_values', 'tables')
    max_reviewing_rounds: int = 1
    user_initiation_prompt: str = dedent_triple_quote_str("""
        In scientific papers, we typically refer to one or two tables summarizing the main findings.

        Based on the material provided above ({actual_background_product_names}), please rewrite \
        the "{pretty_section_names}" while referring to the relevant Tables".

        In addition, change the text to refer to the tables (use their labels if necessary),
        so that the tables are incorporated as integral part of the {pretty_section_names}.
        """)


@dataclass
class PaperSectionWithTablesReviewGPT(PaperSectionReviewGPT):
    goal_verb: str = 'add tables to'
    user_agent: ScientificAgent = ScientificAgent.TableExpert
    background_product_fields = ('results_summary', 'data_analysis_code_and_output', 'title_and_abstract')
    max_reviewing_rounds: int = 1
    user_initiation_prompt: str = dedent_triple_quote_str("""
        In scientific papers, we typically add one or two tables summarizing the main findings.

        Based on the material provided above ({actual_background_product_names}), please rewrite \
        the "{pretty_section_names}" while adding relevant Tables".

        The tables should only include information that is explicitly extracted from the results data.
        Add the tables centered in booktabs, multirow format with caption and label. 
        In addition, change the text to refer to the tables (use their labels if necessary),
        so that the tables are incorporated as integral part of the {pretty_section_names} section. 
        Do not add figures, only add tables.
        Write the section with tables in tex format including \\section{} command, and any math or symbols that \
        needs tex escapes.
        """)

    @property
    def actual_background_product_fields(self) -> Tuple[str, ...]:
        return super().actual_background_product_fields + ('most_updated_paper_sections:' + self.section_name, )
