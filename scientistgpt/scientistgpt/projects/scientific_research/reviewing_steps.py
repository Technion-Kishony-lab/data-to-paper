from dataclasses import dataclass, field
from typing import Tuple, Dict, Any

from scientistgpt.servers.openai_models import ModelEngine
from scientistgpt.utils import dedent_triple_quote_str
from scientistgpt.utils.nice_list import NiceDict
from scientistgpt.base_steps import BaseProductsQuotedReviewGPT, LatexReviewBackgroundProductsConverser, \
    PythonValueReviewBackgroundProductsConverser, CheckExtractionReviewBackgroundProductsConverser

from .cast import ScientificAgent
from .scientific_products import ScientificProducts


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
    CHATGPT_PARAMETERS = {'temperature': 1.0}
    max_reviewing_rounds: int = 1
    background_product_fields: Tuple[str, ...] = ('data_file_descriptions', 'codes_and_outputs:data_exploration')
    conversation_name: str = 'research_goal'
    other_conversation_name: str = 'research_goal_reviewer'
    goal_noun: str = 'research goal and hypothesis'
    goal_verb: str = 'suggest'
    assistant_agent: ScientificAgent = ScientificAgent.Performer
    user_agent: ScientificAgent = ScientificAgent.GoalReviewer
    termination_phrase: str = \
        'I hereby approve the research goal'
    user_initiation_prompt: str = dedent_triple_quote_str("""
        Please suggest a research goal and an hypothesis. 
        The goal and hypothesis should be interesting and novel. 
        Try to avoid trivial hypotheses (like just testing for simple linear relationships). 
        
        Do not suggest methodology. Just the goal and hypothesis. 
        Make sure that your suggested hypothesis can be studied using only the provided dataset, 
        without requiring any additional data \
        (pay attention to using only data available based on the provided headers of the our data files \
        as in the description of our dataset, above).

        {quote_request}.
        """)
    quote_request: str = 'Please return the goal and hypothesis enclosed within triple-backticks ' \
                         '(make sure to flank the entire goal and hypotheses, not just their header).'
    other_system_prompt: str = dedent_triple_quote_str("""
        You are a {reviewer} for a {performer} who needs to {goal_verb} {goal_noun}.
        """)
    sentence_to_add_at_the_end_of_performer_response: str = dedent_triple_quote_str("""
        
        Please provide constructive bullet point feedback on the above {goal_noun}.
        
        Specifically: 
        (1) Whether the hypothesis can be tested using only the provided dataset (without \
        requiring additional data).
        (2) Whether the hypothesis is interesting and novel.
        (3) If the hypothesis is broad or convoluted, which of the questions it proposes is best to focus on \
        for further research.
        
        
        Do not provide positive feedback; if these conditions are all satisfied, just respond with: 
        "{termination_phrase}" (approving-phrase).
        If you feel that the initial goal and hypothesis fully satisfy the above conditions, \
        you can respond with with approving-phrase \
        immediately, without requesting any improvement cycles.
    """)

    sentence_to_add_at_the_end_of_reviewer_response = 2


@dataclass
class PlanReviewGPT(ScientificProductsQuotedReviewGPT):
    max_reviewing_rounds: int = 1  # 0 for no review cycles
    background_product_fields: Tuple[str, ...] = ('data_file_descriptions', 'codes_and_outputs:data_exploration',
                                                  'research_goal')
    conversation_name: str = 'analysis_plan'
    goal_noun: str = 'short data analysis plan'
    goal_verb: str = 'write'
    user_initiation_prompt: str = dedent_triple_quote_str("""
        Please {goal_verb} {goal_noun}. 
        Do not include any data visualization steps.
        Explicitly specify all relevant analysis results and values that should be calculated.
        If there are any specific statistical tests that should be performed, specify how they should be performed.

        Do not specify data exploration steps, as they are already performed.
        {quote_request}
        """)
    assistant_agent: ScientificAgent = ScientificAgent.Performer
    user_agent: ScientificAgent = ScientificAgent.PlanReviewer


@dataclass
class HypothesesTestingPlanReviewGPT(ScientificProductsQuotedReviewGPT):
    max_reviewing_rounds: int = 1  # 0 for no review cycles
    background_product_fields: Tuple[str, ...] = ('data_file_descriptions', 'outputs:data_exploration',
                                                  'codes:data_preprocessing', 'research_goal')
    conversation_name: str = 'hypothesis_testing_plan'
    goal_noun: str = 'hypothesis testing plan'
    goal_verb: str = 'write'
    user_initiation_prompt: str = dedent_triple_quote_str("""
        Please {goal_verb} an {goal_noun}. 
        Do not include any data exploration, preprocessing, loading or visualization steps. \
        You should specifically refer to the hypotheses listed above.
        For each of the hypotheses, specify the statistical test that should be performed to test it.
        If there are several possible tests, specify only one (the simplest one).

        {quote_request}
        """)
    assistant_agent: ScientificAgent = ScientificAgent.Performer
    user_agent: ScientificAgent = ScientificAgent.PlanReviewer


@dataclass
class TablesNamesReviewGPT(PythonValueReviewBackgroundProductsConverser):
    products: ScientificProducts = None
    max_reviewing_rounds: int = 0
    background_product_fields: Tuple[str] = ('data_file_descriptions', 'codes:data_preprocessing',
                                             'codes:data_analysis', 'outputs:data_analysis', 'research_goal')
    conversation_name: str = 'table_names'
    value_type: type = Dict[str, str]
    goal_noun: str = 'names of tables for a research paper'
    goal_verb: str = 'come up with'
    assistant_agent: ScientificAgent = ScientificAgent.Performer
    user_agent: ScientificAgent = ScientificAgent.TableExpert
    user_initiation_prompt: str = dedent_triple_quote_str("""
        Please list captions for Tables for a scientific paper that will capture the most important results we have.
        You can only give names of tables that can be produced from data that found within the data exploration \
        and data analysis outputs (see above).
        
        The table names that you choose should be returned as a Python Dict[str, str], with the keys \
        in the form of 'Table n' and the values being the actual names of the tables.
        
        For example, you might return the following:        
        {
            'Table 1': 'Summary of the results of the linear regression model results',
            'Table 2': 'Summary of the statistical analysis of the most important linear regression model coefficients',
        }
        
        Obviously, this is just an example. You should choose the table names that are most relevant to the specific \
        results we got in the output and in light of the overall goal of the project as mentioned above. 
        The names should accurately describe the tables that will be produced in a later stage.
        Do not suggest tables names that mention data and results that are not found in the provided outputs.
        
        Typically, a scientific paper has up to 3 tables, each containing completely unique and different results.
        You need to choose names for a maximum of 3 tables you think are needed to cover the most important \
        scientific results as presented to you above.
        Don't suggest name of tables which are not completely necessary, or technical or \
        irrelevant to the research goal.
        Also, do not suggest names of tables that may require additional data that is not found in the provided outputs.
        
        Do not send any free text; Your response should be structured as a Python Dict[str, str].
        """)

    sentence_to_add_at_the_end_of_performer_response: str = dedent_triple_quote_str("""
        Please provide feedback on the above table names, with specific attention to whether they are \
        relevant to the research goal, and can be created solely from information that provided in our output data.

        If you are satisfied, respond with "{termination_phrase}".
        """)

    def _check_response_value(self, response_value: Any) -> Any:
        return NiceDict(response_value)


@dataclass
class TablesReviewBackgroundProductsConverser(LatexReviewBackgroundProductsConverser,
                                              CheckExtractionReviewBackgroundProductsConverser):
    products: ScientificProducts = None
    max_reviewing_rounds: int = 1
    background_product_fields: Tuple[str, ...] = ('data_file_descriptions', 'codes:data_preprocessing',
                                                  'codes:data_analysis', 'outputs:data_analysis', 'research_goal',
                                                  'tables_and_tables_names')
    table_name: str = None
    product_fields_from_which_response_is_extracted: Tuple[str] = ('outputs:data_exploration', 'outputs:data_analysis',)
    conversation_name: str = 'tables'
    goal_noun: str = 'table for a scientific paper'
    goal_verb: str = 'produce'
    model_engine: ModelEngine = field(default_factory=lambda: ModelEngine.GPT4)
    assistant_agent: ScientificAgent = ScientificAgent.Performer
    user_agent: ScientificAgent = ScientificAgent.TableExpert
    termination_phrase: str = 'I hereby approve the table'
    user_initiation_prompt: str = dedent_triple_quote_str("""
        Please build the table "{table_name}". 
        You should build the table using the results provided in the output files above.
        The table should only include information that is explicitly extracted from these outputs.
        The table should have a caption suitable for inclusion as part of a scientific paper.
        When mentioning p-values, use the $<$ symbol to indicate that the p-value is smaller than the relevant value, \
        in scientific writing it is not common to write 0 as a p-value.
        {do_not_repeat_information_from_previous_tables}
        
        Write the table in latex format, centered, in booktabs, multirow format with caption and label.
        Make sure that the table is not too wide, so that it will fit within document text width.
        """)

    sentence_to_add_at_the_end_of_performer_response: str = dedent_triple_quote_str("""
        Please provide actionable feedback on the above table, with specific attention to whether the table \
        contains only information that is explicitly extracted from the results data. Compare the numbers in the table \
        to the numbers in the results data and explicitly mention any discrepancies that need to get fixed.
        Notice that each tables should contain unique information - it is not acceptable to have two tables \
        that contain the same column or even partial overlap of results. 
        Do not suggest changes to the table that may require data not available in our dataset.
        If you are satisfied, respond with "{termination_phrase}".
        NOTICE: If you give any type of feedback, you cannot reply with "{termination_phrase}".
        """)

    @property
    def num_of_existing_tables(self) -> int:
        return len(self.products.all_tables)

    @property
    def table_number(self) -> int:
        return self.num_of_existing_tables + 1

    @property
    def total_number_of_tables(self) -> int:
        return len(self.products.tables_names)

    @property
    def do_not_repeat_information_from_previous_tables(self) -> str:
        if self.num_of_existing_tables > 0:
            return dedent_triple_quote_str("""
                Notice that the table should only add new information that is not included already \
                in the {} we already build (see above).
                """).format('table' if self.num_of_existing_tables == 1 else 'tables')
        else:
            return ''

    def _get_latex_section_from_response(self, response: str, section_name: str) -> str:
        section = super()._get_latex_section_from_response(response, section_name)
        return self._check_extracted_numbers(section)


@dataclass
class KeyNumericalResultsExtractorReviewGPT(PythonValueReviewBackgroundProductsConverser,
                                            CheckExtractionReviewBackgroundProductsConverser):
    max_reviewing_rounds: int = 1
    background_product_fields: Tuple[str, ...] = ('research_goal', 'outputs:data_exploration', 'outputs:data_analysis',
                                                  'tables')
    product_fields_from_which_response_is_extracted: Tuple[str, ...] = (
        'outputs:data_exploration', 'outputs:data_analysis')
    conversation_name: str = 'key_numerical_results_extractor'
    value_type: type = Dict[str, Any]
    goal_noun: str = 'key numerical values'
    goal_verb: str = 'extract'
    model_engine: ModelEngine = field(default_factory=lambda: ModelEngine.GPT4)
    assistant_agent: ScientificAgent = ScientificAgent.Performer
    user_agent: ScientificAgent = ScientificAgent.InterpretationReviewer
    user_initiation_prompt: str = dedent_triple_quote_str("""
        Please {goal_verb} {goal_noun} that capture the most important results we got in the output.
        The {goal_noun} you choose should be those that are not presented in the latex paper tables above but \
        might still be needed for a scientific paper.
        These {goal_noun} should only include information that is explicitly extracted from the output files provided \
        above.
        The {goal_noun} that you choose should be returned as a Python Dict[str, Any], where the keys are the names \
        tou choose for the result, and the values are the numeric results themselves.
        For example, if the analysis results provide summary of a some statistical tests, or statistical models, \
        you might include: 
        {
            'Accuracy of logistic regression for the XXX model': 0.835,
            'AUC ROC of logistic regression for the XXX model': 0.77,
        }
        Obviously, this is just an example. You should choose the {goal_noun} that are most relevant to the specific \
        results we got in the output and in light of the overall goal of the project as mentioned above.

        Do not send any free text. All descriptions should be included in the keys of the Python Dict.
        Be judicious when choosing values; a scientific paper will typically mention 3-10 important values.
        """)
    sentence_to_add_at_the_end_of_performer_response: str = dedent_triple_quote_str("""
        Please provide feedback on the above {goal_noun}, with specific attention to whether they \
        contain only information that is explicitly extracted from the provided output data. Compare the numbers 
        in the provided Python dict values with the numbers in the result output data and explicitly mention \
        any discrepancies that need to get fixed.

        If you are satisfied, respond with "{termination_phrase}".
        """)

    def _extract_str_of_python_value_from_response(self, response: str) -> str:
        extracted_str = super()._extract_str_of_python_value_from_response(response)
        return self._check_extracted_numbers(extracted_str)

    def _check_response_value(self, response_value: Any) -> Any:
        return NiceDict(response_value)


@dataclass
class ResultsInterpretationReviewGPT(ScientificProductsQuotedReviewGPT):
    max_reviewing_rounds: int = 1
    background_product_fields: Tuple[str, ...] = ('data_file_descriptions', 'research_goal',
                                                  'tables_and_numeric_values')
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
    user_initiation_prompt: str = "Please {goal_verb} {goal_noun}. " + \
                                  "Briefly mention the tools used to preform the analysis.\n\n" \
                                  "{quote_request}"
