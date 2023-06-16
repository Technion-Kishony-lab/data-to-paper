import re
from dataclasses import dataclass
from typing import Tuple, Dict, Any

from data_to_paper.servers.openai_models import ModelEngine
from data_to_paper.utils import dedent_triple_quote_str
from data_to_paper.utils.nice_list import NiceDict
from data_to_paper.base_steps import BaseProductsQuotedReviewGPT, LatexReviewBackgroundProductsConverser, \
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

        Do not suggest methodology. Just the goal and an hypothesis. 
        Make sure that your suggested hypothesis can be studied using only the provided dataset, \
        without requiring any additional data \
        (pay attention to using only data available based on the provided headers of our data files \
        as in the description of the original dataset, above).

        {quote_request}
        """)
    quote_request: str = 'Please return the goal and hypothesis enclosed within triple-backticks ' \
                         '(make sure to flank the entire goal and hypotheses, not just their header).'
    other_system_prompt: str = dedent_triple_quote_str("""
        You are a {reviewer} for a {performer} who needs to {goal_verb} {goal_noun}.
        """)
    sentence_to_add_at_the_end_of_performer_response: str = dedent_triple_quote_str("""

        Please provide constructive bullet point feedback on the above {goal_noun}.

        Specifically: 
        * If the hypothesis cannot be tested using only the provided dataset (without \
        requiring additional data), suggest how to modify the hypothesis to better fit the dataset.
        * If the hypothesis is not interesting and novel, suggest how to modify it to make it more interesting.
        * If the hypothesis is broad or convoluted, suggest how best to focus it on a single well defined question.


        Do not provide positive feedback; if these conditions are all satisfied, just respond with: 
        "{termination_phrase}".
        If you feel that the initial goal and hypothesis satisfy the above conditions, \
        respond solely with "{termination_phrase}".
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
class HypothesesTestingPlanReviewGPT(PythonValueReviewBackgroundProductsConverser):
    value_type: type = Dict[str, str]
    max_valid_response_iterations: int = 4
    max_reviewing_rounds: int = 0  # 0 for no review cycles
    background_product_fields: Tuple[str, ...] = ('data_file_descriptions', 'codes_and_outputs:data_exploration',
                                                  'research_goal')
    conversation_name: str = 'hypothesis_testing_plan'
    goal_noun: str = 'hypothesis testing plan'
    goal_verb: str = 'write'
    user_initiation_prompt: str = dedent_triple_quote_str("""
        We would like to test the specified hypotheses using the provided dataset.

        In light of the dataset description and the data exploration output provided above, \
        for each of the following generic \
        statistical issues determine if they are relevant for our case and whether they should be accounted for: 

        * multiple comparisons.
        * confounding variables (see available variables in the dataset that we can adjust for).
        * dependencies between data points.
        * missing data points.
        * any other relevant statistical issues.

        Then, for each hypothesis, suggest a *single* statistical test that should be performed to test the hypothesis \
        and specify how it should be used while accounting for any issues above that you deem relevant.
        If there are several possible ways to test a given hypothesis, specify only *one* statistical test \
        (the simplest one).

        Return your suggested statistical tests as a Python dictionary Dict[str, str], \
        where the keys briefly specify the hypotheses and the values are the suggested statistical tests. For example:

        { 
        'xxx is associated with yyy': 'linear regression with xxx as the independent variable and \
        yyy as the dependent variable while adjusting for zzz1, zzz2, zzz3',
        'the variance of xxx is different than the variance of yyy': 'F-test for the equality of variances',
        }
        """)
    assistant_agent: ScientificAgent = ScientificAgent.Performer
    user_agent: ScientificAgent = ScientificAgent.PlanReviewer

    def _check_response_value(self, response_value: Any) -> Any:
        """
        Strip "hypothesis x" from the keys of the response value.
        """
        new_response_value = {}
        for k in response_value.keys():
            new_k = re.sub(r'hypothesis \d+:', '', k, flags=re.IGNORECASE).strip()
            new_response_value[new_k] = response_value[k]
        return NiceDict(new_response_value)


@dataclass
class TablesNamesReviewGPT(PythonValueReviewBackgroundProductsConverser):
    products: ScientificProducts = None
    max_reviewing_rounds: int = 1
    background_product_fields: Tuple[str] = ('data_file_descriptions', 'codes:data_preprocessing',
                                             'codes:data_analysis', 'outputs:data_analysis', 'research_goal',
                                             'hypothesis_testing_plan')
    conversation_name: str = 'table_names'
    value_type: type = Dict[str, str]
    goal_noun: str = 'names of tables for a research paper'
    goal_verb: str = 'suggest'
    assistant_agent: ScientificAgent = ScientificAgent.Performer
    user_agent: ScientificAgent = ScientificAgent.TableExpert
    termination_phrase: str = 'I hereby approve the names of the tables'
    user_initiation_prompt: str = dedent_triple_quote_str("""
        Please list captions for Tables that we should prepare for a scientific paper addressing the research goal and \
        hypothesis testing described above.

        The table names that you choose should be returned as a Python Dict[str, str], with the keys \
        in the form of 'Table n' and the values being the actual names of the tables.

        For example, you might return the following:        
        {
            'Table 1': 'Summary statistics of the dataset',
            'Table 2': 'Test for association of xxx with yyy (Linear Regression)',
            'Table 3': 'Factors affecting zzz and their interactions (Two Way ANOVA)',
        }

        Obviously, this is just an example. You should choose table names that suit the dataset, the research goal \
        and the hypotheses we are testing.
        The names you choose should accurately describe the tables that will be produced in a later stage.

        Typically, a scientific paper has up to 2 tables, each containing completely unique and different results.
        You need to choose names for a maximum of 1-3 tables that will each present distinct non-overlapping \
        information.

        Don't suggest name of tables that are:
        * Not completely necessary.
        * Represent technical information, rather than scientific results.
        * Irrelevant to the research goal, or that cannot be created from the dataset provided.
        * Overlapping with other tables in your list. 

        Do not send any free text; Your response should be structured as a Python Dict[str, str].
        """)

    sentence_to_add_at_the_end_of_performer_response: str = dedent_triple_quote_str("""
        Please provide feedback on the above table names, with specific attention to whether they are \
        representing all the hypotheses we are testing, and can be created solely from the dataset provided.

        If you are satisfied, respond with "{termination_phrase}".
        """)

    def _check_response_value(self, response_value: Any) -> Any:
        return NiceDict(response_value)


@dataclass
class TablesReviewBackgroundProductsConverser(LatexReviewBackgroundProductsConverser,
                                              CheckExtractionReviewBackgroundProductsConverser):
    products: ScientificProducts = None
    max_reviewing_rounds: int = 0
    model_engine: ModelEngine = ModelEngine.GPT4
    background_product_fields: Tuple[str, ...] = ('data_file_descriptions', 'codes:data_preprocessing',
                                                  'codes:data_analysis', 'outputs:data_analysis', 'research_goal',
                                                  'tables_and_tables_names')
    table_name: str = None
    product_fields_from_which_response_is_extracted: Tuple[str] = \
        ('data_file_descriptions', 'outputs:data_exploration', 'outputs:data_analysis',)
    conversation_name: str = 'tables'
    goal_noun: str = 'table for a scientific paper'
    goal_verb: str = 'produce'
    assistant_agent: ScientificAgent = ScientificAgent.Performer
    user_agent: ScientificAgent = ScientificAgent.TableExpert
    termination_phrase: str = 'I hereby approve the table'
    user_initiation_prompt: str = dedent_triple_quote_str("""
        Please build the table "{table_name}". 
        You should build the table using the results provided in the output files above.
        The table should only include information that is explicitly extracted from these outputs.

        Important: You do NOT need to include all the information from the outputs, just include the information that \
        is relevant and suitable for inclusion in a table of a scientific paper.

        As appropriate, you should:
        * Exclude and re-order rows/columns.
        * Organize the table sensibly.  
        * Re-name technical names to scientifically-suitable names.
        * Rename technical values (like 0/1) to scientifically-suitable values (like "No"/"Yes").
        * Use proper scientific notation for numbers and round numbers to a reasonable number of digits.
        * Indicate standard errors using the $\\pm$ symbol, or parentheses.
        * Add a caption suitable for inclusion as part of a scientific paper \
        (you can use the table name provided above, or modify it as you see fit).
        * If you indicate p-values, you can use the $<$ symbol to indicate smaller than a given value, \
        (any p-value less than 10^-4 should be indicated as $<$10^{-4}).

        {do_not_repeat_information_from_previous_tables}
        Write the table in latex format, centered, in booktabs, multirow format with caption and label.
        Make sure that the table is not too wide, so that it will fit within document text width.
        """)

    sentence_to_add_at_the_end_of_performer_response: str = dedent_triple_quote_str("""
        Please provide actionable feedback on the above table, with specific attention to whether the table \
        correctly represent data from our analysis output.

        {do_not_repeat_information_from_previous_tables}

        Do not suggest changes to the table that may require data not available in our dataset.
        Do not return the modified table itself, just write comments on how to improve it.

        If you don't see any issues, respond with "{termination_phrase}".
        NOTICE: If you give any type of constructive feedback, do not include "{termination_phrase}" in your response.
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
                in the {} we already built (see above).
                """).format('table' if self.num_of_existing_tables == 1 else 'tables')
        else:
            return ''

    def _get_latex_section_from_response(self, response: str, section_name: str) -> str:
        section = super()._get_latex_section_from_response(response, section_name)
        return self._check_extracted_numbers(section)


@dataclass
class KeyNumericalResultsExtractorReviewGPT(PythonValueReviewBackgroundProductsConverser,
                                            CheckExtractionReviewBackgroundProductsConverser):
    max_reviewing_rounds: int = 0
    background_product_fields: Tuple[str, ...] = ('research_goal', 'outputs:data_exploration', 'outputs:data_analysis',
                                                  'tables')
    product_fields_from_which_response_is_extracted: Tuple[str, ...] = (
        'outputs:data_exploration', 'outputs:data_analysis')
    conversation_name: str = 'key_numerical_results_extractor'
    value_type: type = Dict[str, Any]
    goal_noun: str = 'key numerical values'
    goal_verb: str = 'extract'
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
            'Total number of samples': xxx,
            'Accuracy of logistic regression for the XXX model': yyy,
            'AUC ROC of logistic regression for the XXX model': zzz,
        }
        Obviously, this is just an example. You should choose the {goal_noun} that are most relevant to the specific \
        results we got in the output and in light of the overall goal of the project as mentioned above.

        Return a maximum of 5 {goal_noun}.
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
