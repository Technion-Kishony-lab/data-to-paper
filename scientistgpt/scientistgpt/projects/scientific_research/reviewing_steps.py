from dataclasses import dataclass, field
from typing import Tuple, Dict, Any

from scientistgpt.utils import dedent_triple_quote_str
from scientistgpt.utils.nice_list import nicely_join
from scientistgpt.base_steps import BaseProductsQuotedReviewGPT, BaseLatexProductsReviewGPT, \
    BasePythonValueProductsReviewGPT

from .cast import ScientificAgent
from ...servers.openai_models import ModelEngine


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
    background_product_fields = ('data_file_descriptions', 'codes_and_outputs:data_exploration')
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
    background_product_fields = ('data_file_descriptions', 'codes_and_outputs:data_exploration', 'research_goal')
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
class TablesReviewGPT(BaseLatexProductsReviewGPT):
    max_reviewing_rounds: int = 1
    background_product_fields = ('research_goal', 'outputs:data_exploration', 'outputs:data_analysis', 'tables')
    conversation_name: str = 'tables'
    goal_noun: str = 'table for a scientific paper'
    goal_verb: str = 'produce'
    model_engine: ModelEngine = field(default_factory=lambda: ModelEngine.GPT4)
    assistant_agent: ScientificAgent = ScientificAgent.Performer
    user_agent: ScientificAgent = ScientificAgent.TableExpert
    table_number: int = 1
    total_number_of_tables: int = 1
    user_initiation_prompt: str = dedent_triple_quote_str("""
        Please {goal_verb} a {goal_noun} that summarize the key results we got in the code analysis output.
        The table should only include information that is explicitly extracted from the results data.
        {do_not_repeat_information_from_previous_tables} 
        The table should be centered, in booktabs, multirow format with caption and label.
        Make sure that the table is not too wide, so that it will fit within document text width.
        Do not write code! write the table in latex format.
        This is table number {table_number} out of {total_number_of_tables} you need to produce, plan the tables \
        so that each table will show unique information.
        """)
    sentence_to_add_at_the_end_of_performer_response: str = dedent_triple_quote_str("""
        Please provide feedback on the above table, with specific attention to whether the table \
        contains only information that is explicitly extracted from the results data. Compare the numbers in the table \
        to the numbers in the results data and explicitly mention any discrepancies that need to get fixed.
        Do not suggest changes to the table that may require data not available in our dataset.
        If you are satisfied, respond with "{termination_phrase}".
        """)

    @property
    def do_not_repeat_information_from_previous_tables(self) -> str:
        if self.products.tables:
            return dedent_triple_quote_str("""
                Notice that the table should add new information that is not already in the tables provided above.
                """)
        else:
            return ''


@dataclass
class KeyNumericalResultsExtractorReviewGPT(BasePythonValueProductsReviewGPT):
    max_reviewing_rounds: int = 1
    background_product_fields = ('research_goal', 'outputs:data_exploration', 'outputs:data_analysis')
    conversation_name: str = 'key_numerical_results_extractor'
    value_type: type = Dict[str, Any]
    goal_noun: str = 'key numerical values'
    goal_verb: str = 'extract'
    assistant_agent: ScientificAgent = ScientificAgent.Performer
    user_agent: ScientificAgent = ScientificAgent.InterpretationReviewer
    user_initiation_prompt: str = dedent_triple_quote_str("""
        Please {goal_verb} {goal_noun} that capture the essence of the results we got in the output.
        The {goal_noun} you choose should be those that cannot be presented in tables but are that we might \
        want to include in a scientific paper.
        These {goal_noun} should only include information that is explicitly extracted from the output of our \
        analysis code.
        The {goal_noun} that you choose should be returned as a Python Dict[str, Any], where the keys are the names 
        of the numerical results, and the values are the numeric values themselves.
        For example, if the analysis results provide summary of a some statistical tests, or statistical models, \
        you might include: 
        {
            'accuracy of logistic regression for the XXX model': 0.835,
            'AUC ROC of logistic regression for the XXX model': 0.77,
        }
        Obviously, this is just an example. You should choose the {goal_noun} that are most relevant to the specific \
        results we got in the output and in light of the overall goal of the project as mentioned above.
        """)
    sentence_to_add_at_the_end_of_performer_response: str = dedent_triple_quote_str("""
        Please provide feedback on these above {goal_noun}, with specific attention to whether they \
        contain only information that is explicitly extracted from the results data. Compare the numbers in the \
        provided Python dict values to the numbers in the results data and explicitly mention \
        any discrepancies that need to get fixed.

        If you are satisfied, respond with "{termination_phrase}".
        """)


@dataclass
class ResultsInterpretationReviewGPT(ScientificProductsQuotedReviewGPT):
    max_reviewing_rounds: int = 1
    background_product_fields = ('data_file_descriptions', 'research_goal', 'codes_and_outputs:data_analysis')
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
        Make sure that the section is grounded in the information provided above and is consistent with it.
        If you find any inconsistencies or discrepancies, please mention them explicitly in your feedback.
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
    background_product_fields = ('data_file_descriptions', 'research_goal', 'codes:data_analysis', 'title_and_abstract',
                                 'most_updated_paper_sections:results', 'most_updated_paper_sections:discussion')
    latex_instructions: str = dedent_triple_quote_str("""
        Write in tex format including the \\section{} command, and any math or symbols that needs tex escapes.
        """)
    sentence_to_add_at_the_end_of_performer_response: str = dedent_triple_quote_str("""
        Please provide constructive feedback on the above {pretty_section_names} for my paper.
        Make sure that the section is grounded in the information provided above and is consistent with it.
        If you find any inconsistencies or discrepancies, please mention them explicitly in your feedback.
        If you are satisfied, respond with "{termination_phrase}".
        """)


@dataclass
class MethodPaperSectionReviewGPT(PaperSectionReviewGPT):
    background_product_fields = ('data_file_descriptions', 'research_goal', 'codes:data_preprocessing',
                                 'codes:data_analysis', 'title_and_abstract')
    max_reviewing_rounds: int = 1
    model_engine: ModelEngine = field(default_factory=lambda: ModelEngine.GPT4)
    user_initiation_prompt: str = dedent_triple_quote_str("""
        Based on the material provided above ({actual_background_product_names}), please write \
        the "{pretty_section_names}" of the paper.
        Make sure that you are only referring to analysis steps that are explicitly performed by the \
        data preprocessing code and data analysis code (see Python blocks above).

        Focus on the methods that were used to achieve the research goal.

        {latex_instructions}
        """)

    sentence_to_add_at_the_end_of_performer_response: str = dedent_triple_quote_str("""
        Please provide constructive feedback on the above {pretty_section_names} for my paper.

        Specifically, pay attention to:
        * Over-specific description of tools, like specifying exact software or package versions used in the analysis.
        * Description of analysis steps that were not performed by the analysis Python codes \
        (provided above), like certain data cleaning processes.
        * References to variables and data files that were not used in the analysis.

        Make sure that the section is grounded in the information provided above and is consistent with it.
        If you find any inconsistencies or discrepancies, please mention them explicitly in your feedback.
        If you are satisfied, respond with "{termination_phrase}".
        """)


@dataclass
class PaperSectionReferringTablesReviewGPT(PaperSectionReviewGPT):
    goal_verb: str = 'refer to tables in'
    user_agent: ScientificAgent = ScientificAgent.TableExpert
    background_product_fields = ('title_and_abstract', 'numerical_values', 'tables_and_numeric_values')
    max_reviewing_rounds: int = 1
    user_initiation_prompt: str = dedent_triple_quote_str("""
        Based on the material provided above ({actual_background_product_names}), please write \
        the "{pretty_section_names}" of the paper, while explicitly \
        mentioning any key Numerical Values that are scientifically meaningful.
        Don't refer to the Numerical Values, explicitly mention them as integral part of the text, as they are \
        not going to be added as a part of the paper otherwise. 
        Refer to the Tables by their labels and explain their content, but do not add the tables themselves \
        (I will add the tables later manually).
        Make sure that you are only mentioning details that are explicitly found within the Tables and Numerical Values.
        {latex_instructions}
        """)
    sentence_to_add_at_the_end_of_performer_response: str = dedent_triple_quote_str("""
        Please provide feedback on the above {goal_noun}, with specific attention to whether the {goal_noun} \
        contain only information that is explicitly extracted from the Tables and Numerical Values provided above. \
        Compare the numbers in the {goal_noun} to the numbers in the Tables and Numerical Values and explicitly \
        mention any discrepancies that need to get fixed.
        Do not suggest changes to the {goal_noun} that may require data not available in the the \
        Tables and Numerical Values.
        If you are satisfied, respond with "{termination_phrase}".
        """)


@dataclass
class PaperSectionWithTablesReviewGPT(PaperSectionReviewGPT):
    goal_verb: str = 'add tables to'
    user_agent: ScientificAgent = ScientificAgent.TableExpert
    background_product_fields = ('results_summary', 'codes_and_outputs:data_analysis', 'title_and_abstract')
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
