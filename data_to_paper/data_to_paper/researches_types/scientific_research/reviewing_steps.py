import re
from dataclasses import dataclass, field
from typing import Tuple, Dict, Any, Optional, Iterable, List

from data_to_paper.servers.openai_models import ModelEngine
from data_to_paper.utils import dedent_triple_quote_str
from data_to_paper.base_steps import BaseProductsQuotedReviewGPT, LatexReviewBackgroundProductsConverser, \
    PythonDictReviewBackgroundProductsConverser, CheckExtractionReviewBackgroundProductsConverser, \
    PythonDictWithDefinedKeysAndValuesReviewBackgroundProductsConverser
from data_to_paper.base_steps.result_converser import Rewind
from data_to_paper.latex.clean_latex import escape_special_chars_and_symbols_in_table
from data_to_paper.latex.tables import get_table_label
from data_to_paper.servers.types import Citation

from .cast import ScientificAgent
from .scientific_products import ScientificProducts
from .writing_steps import ShowCitationProducts


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
        'The research goal does not require any changes'

    goal_guidelines: str = dedent_triple_quote_str("""\n
        Guidelines:

        * Try to avoid trivial hypotheses (like just testing for simple linear associations).
        Instead, you could perhaps explore more complex associations and relationships, like testing for \
        mediation, or moderation effects, or interactions between variables. 

        * Make sure that your suggested hypothesis can be studied using only the provided dataset, \
        without requiring any additional data. In particular, pay attention to using only data available \
        based on the provided headers of our data files (see "{data_file_descriptions}", above).

        * Avoid goals and hypotheses that involve ethic issues like sociodemographic (Income, Education, etc.) \
        and psychological (Mental Health) variables. 
        Note though that you can, and should, still use these as confounding variables if needed.

        * Do not suggest methodology. Just the goal and an hypothesis. 
        """)
    user_initiation_prompt: str = dedent_triple_quote_str("""\n
        Please suggest a research goal and an hypothesis that can be studied using only the provided dataset. 
        The goal and hypothesis should be interesting and novel.
        {goal_guidelines}
        {quote_request}
        """)
    quote_request: str = dedent_triple_quote_str("""
        INSTRUCTIONS FOR FORMATTING YOUR RESPONSE:
        Please return the goal and hypothesis enclosed within triple-backticks, like this:
        ```
        Research Goal: 
        <your research goal here>

        Hypothesis: 
        <your hypothesis here>
        ```
        """)
    other_system_prompt: str = dedent_triple_quote_str("""
        You are a {reviewer} for a {performer} who needs to {goal_verb} {goal_noun}.
        """)
    sentence_to_add_at_the_end_of_performer_response: str = dedent_triple_quote_str("""

        Please provide constructive bullet-point feedback on the above {goal_noun}.

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


@dataclass
class GetMostSimilarCitations(ShowCitationProducts, PythonDictReviewBackgroundProductsConverser):
    products: ScientificProducts = None
    allow_citations_from_step: str = 'goal'
    max_reviewing_rounds: int = 0

    model_engine: ModelEngine = ModelEngine.GPT4
    value_type: type = Dict[str, str]
    goal_noun: str = 'most similar papers'
    goal_verb: str = 'find'
    assistant_agent: ScientificAgent = ScientificAgent.Performer
    user_agent: ScientificAgent = ScientificAgent.GoalReviewer
    conversation_name: str = 'similar_citations'
    is_new_conversation: bool = None  # this will create "similar_citations_0", etc.
    background_product_fields: Tuple[str, ...] = ('data_file_descriptions', 'research_goal',
                                                  'literature_search:goal:dataset', 'literature_search:goal:questions')
    rewind_after_getting_a_valid_response: Rewind = Rewind.REPOST_AS_FRESH

    user_initiation_prompt: str = dedent_triple_quote_str("""
        From the literature search above, list up to 5 key papers whose results are most \
        similar/overlapping with our research goal and hypothesis.

        Return your response as a Python Dict[str, str], where the keys are bibtex ids of the papers, \
        and the values are the titles of the papers. For example:

        ```python
        {
            "Smith2020TheAB": "A title of a paper most overlapping with our goal and hypothesis",
            "Jones2021AssortedCD": "Another title of a paper that is similar to our goal and hypothesis",
        }
        ```
    """)

    def _check_response_value(self, response_value: Any) -> Any:
        response_value = super()._check_response_value(response_value)
        available_citations = self._get_available_citations()
        bibtex_ids_to_citations: Dict[str, Citation] = \
            {citation.bibtex_id: citation for citation in available_citations}
        non_matching_ids = [key for key in response_value.keys() if key not in bibtex_ids_to_citations]
        if non_matching_ids:
            self._raise_self_response_error(f'Invalid bibtex ids: {non_matching_ids}')

        # replace with correct citation titles
        response_value = type(response_value)({key: bibtex_ids_to_citations[key].title for key in response_value})
        return response_value

    def get_overlapping_citations(self) -> List[Citation]:
        ids_to_titles = self.run_dialog_and_get_valid_result()
        available_citations = self._get_available_citations()
        return [citation for citation in available_citations if citation.bibtex_id in ids_to_titles]


@dataclass
class IsGoalOK(ShowCitationProducts, PythonDictWithDefinedKeysAndValuesReviewBackgroundProductsConverser):
    products: ScientificProducts = None
    model_engine: ModelEngine = ModelEngine.GPT4
    value_type: type = Dict[str, str]
    allowed_values_for_keys: Dict[str, Iterable] = field(default_factory=lambda: {'choice': ('OK', 'REVISE')})
    goal_noun: str = 'research goal and hypothesis'
    goal_verb: str = 'check'
    assistant_agent: ScientificAgent = ScientificAgent.Performer
    user_agent: ScientificAgent = ScientificAgent.GoalReviewer
    conversation_name: str = 'is_goal_ok'
    is_new_conversation: bool = None  # this will create "research_goal_0", etc.
    background_product_fields: Tuple[str, ...] = ('data_file_descriptions', 'research_goal',
                                                  'literature_search:goal:goal and hypothesis')
    rewind_after_getting_a_valid_response: Rewind = Rewind.REPOST_AS_FRESH

    user_initiation_prompt: str = dedent_triple_quote_str("""
        Given the related papers listed above, please follow these 3 steps:

        (1) Provide a bullet-point list of potential similarities between our goal and hypothesis, \
        and the related papers listed above.

        (2) Determine in what ways, if any, our stated goal and hypothesis are distinct from the related papers \
        listed above.

        (3) Given your assessment above, choose one of the following two options:

        a. Our goal and hypothesis offer a significant novelty compared to existing literature, and \
        will likely lead to interesting and novel findings {'choice': 'OK'}.

        b. Our goal and hypothesis have overlap with existing literature, and I can suggest ways to \
        revise them to make them more novel {'choice': 'REVISE'}.

        Your response for this part should be formatted as a Python dictionary mapping 'choice' to \
        either 'OK' or 'REVISE'. 
        Namely, return either: {'choice': 'OK'} or {'choice': 'REVISE'}
        """)

    def is_goal_ok(self):
        return self.run_and_get_valid_result()['choice'] == 'OK'


@dataclass
class ReGoalReviewGPT(GoalReviewGPT):
    is_new_conversation: bool = None
    max_reviewing_rounds: int = 0
    background_product_fields: Tuple[str, ...] = ('data_file_descriptions', 'codes_and_outputs:data_exploration',
                                                  'research_goal', 'literature_search:goal:goal and hypothesis')
    user_initiation_prompt: str = dedent_triple_quote_str("""
        Based on the result of the literature search above, \
        please revise, or completely re-write, the research goal and hypothesis that we have so that they \
        do not completely overlap existing literature.
        {goal_guidelines}
        {quote_request}
        """)


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
class HypothesesTestingPlanReviewGPT(PythonDictReviewBackgroundProductsConverser):
    value_type: type = Dict[str, str]
    max_valid_response_iterations: int = 4
    max_hypothesis_count: int = 3
    max_reviewing_rounds: int = 0  # 0 for no review cycles
    background_product_fields: Tuple[str, ...] = ('data_file_descriptions', 'codes_and_outputs:data_exploration',
                                                  'research_goal')
    conversation_name: str = 'hypothesis_testing_plan'
    is_new_conversation: bool = None  # this will create "hyp_testing_plan_0", etc.
    goal_noun: str = 'hypothesis testing plan'
    goal_verb: str = 'write'
    user_initiation_prompt: str = dedent_triple_quote_str("""
        We would like to test the specified hypotheses using the provided dataset.

        Please follow these two steps:

        (1) Return a bullet-point review of relevant statistical issues.
        Read the "{data_file_descriptions}" and the "{codes_and_outputs:data_exploration}" provided above, \
        and then for each of the following generic \
        statistical issues determine if they are relevant for our case and whether they should be accounted for: 
        * multiple comparisons.
        * confounding variables (see available variables in the dataset that we can adjust for).
        * dependencies between data points.
        * missing data points.
        * any other relevant statistical issues.

        (2) Create a Python Dict[str, str], mapping each hypothesis (dict key) to the statistical test that \
        would be most adequate for testing it (dict value).
        The keys of this dictionary should briefly describe each of our hypotheses.
        The values of this dictionary should specify the most adequate statistical test for each hypothesis, \
        and describe how it should be performed while accounting for any issues you have outlined above as relevant.

        For each of our hypotheses, suggest a *single* statistical test.
        If there are several possible ways to test a given hypothesis, specify only *one* statistical test \
        (the simplest one).

        Your response for this part should be formatted as a Python dictionary, like this:
        ```python
        {
            "xxx is associated with yyy": 
                "linear regression with xxx as the independent variable and  yyy as the dependent variable while \
        adjusting for aaa, bbb, ccc",
            "the above association between xxx and yyy is mediated by zzz":
                "mediation analysis with xxx as the independent \
        variable, yyy as the dependent variable, and zzz as the mediator, while adjusting for aaa, bbb, ccc",
        }
        ```

        Or, here is another example:
        ```python
        {
            "xxx is associated with yyy and zzz":
                "linear regression with xxx as the independent variable and \
        yyy and zzz as the dependent variables while adjusting for aaa, bbb, ccc",
            "the association between xxx and yyy is moderated by zzz": 
                "repeat the above linear regression, \
        while adding the interaction term between yyy and zzz",
        }
        ```

        These of course are just examples. Your actual response should be based on the goal and hypotheses that \
        we have specified above (see the "{research_goal}" above).

        Note how in both cases the the different hypotheses are connected to each other, building towards a single
        study goal.

        Remember to return a valid Python dictionary Dict[str, str].
        """)
    assistant_agent: ScientificAgent = ScientificAgent.Performer
    user_agent: ScientificAgent = ScientificAgent.PlanReviewer

    def _check_response_value(self, response_value: Any) -> Any:
        """
        Strip "hypothesis x" from the keys of the response value.
        """
        response_value = super()._check_response_value(response_value)
        if len(response_value) > self.max_hypothesis_count:
            self._raise_self_response_error(
                f'Please do not specify more than {self.max_hypothesis_count} hypotheses. '
                f'Revise your response to return a maximum of {self.max_hypothesis_count} hypotheses, '
                f'which should all build towards a single study goal.')
        return type(response_value)(
            {re.sub(pattern=r'hypothesis \d+:|hypothesis:|hypothesis :',
                    repl='', string=k, flags=re.IGNORECASE).strip(): v
             for k, v in response_value.items()})


@dataclass
class TablesNamesReviewGPT(PythonDictReviewBackgroundProductsConverser):
    products: ScientificProducts = None
    max_reviewing_rounds: int = 1
    background_product_fields: Tuple[str] = ('data_file_descriptions', 'codes:data_preprocessing',
                                             'codes:data_analysis', 'outputs:data_analysis', 'research_goal',
                                             'hypothesis_testing_plan')
    conversation_name: str = 'table_names'
    value_type: type = Dict[str, str]
    goal_noun: str = 'table captions for a research paper'
    goal_verb: str = 'suggest'
    assistant_agent: ScientificAgent = ScientificAgent.Performer
    user_agent: ScientificAgent = ScientificAgent.TableExpert
    termination_phrase: str = 'The table captions do not require any changes'
    user_initiation_prompt: str = dedent_triple_quote_str("""
        Please list captions for tables that we should prepare for a scientific paper addressing the \
        "{research_goal}" and "{hypothesis_testing_plan}" described above.

        The captions that you choose should be returned as a Python Dict[str, str], with the keys \
        in the form of 'Table n' and the values being the captions of the tables.

        For example, you might return the following:

        ```python
        {
            'Table 1': 'Summary statistics of the dataset',
            'Table 2': 'Test for association of xxx with yyy (Linear Regression)',
            'Table 3': 'Factors affecting zzz and their interactions (Two Way ANOVA)',
        }
        ```

        Obviously, this is just an example. You should choose table captions that suit the dataset, the research goal \
        and the hypotheses we are testing.
        The captions you choose should accurately describe the tables that will be produced in a later stage.

        Typically, a scientific paper has 2-3 tables, each containing completely unique and different results.
        You need to choose captions for a maximum of 1-4 tables that will each present distinct non-overlapping \
        information.

        Do not suggest captions that describe tables that:
        * Are not completely necessary.
        * Represent technical information, rather than scientific results.
        * Are irrelevant to the research goal, or that cannot be created from the dataset provided.
        * Overlap with other tables in your list. 

        Do not send any free text; Your response should be structured as a Python Dict[str, str].
        """)

    sentence_to_add_at_the_end_of_performer_response: str = dedent_triple_quote_str("""\n
        Please check the above chosen suggested tables, with specific attention to whether they \
        represent all the hypotheses we are testing, and can be created solely from the dataset provided.

        If you find any issues, please provide bullet-point feedback.
        Or, if you are satisfied, please respond with "{termination_phrase}".

        Note you must either approve the table captions or provide bullet-point feedback but not both.
        """)

    def _check_response_value(self, response_value: Any) -> Any:
        response_value = super()._check_response_value(response_value)
        if len(response_value) > 4:
            self._raise_self_response_error(f'Please choose a maximum of 4 tables.')
        return response_value


@dataclass
class SecondTablesNamesReviewGPT(TablesNamesReviewGPT):
    max_reviewing_rounds: int = 0
    background_product_fields: Tuple[str] = ('data_file_descriptions', 'codes:data_preprocessing',
                                             'codes:data_analysis', 'outputs:data_analysis')
    conversation_name: str = 'second_table_names'
    value_type: type = Dict[str, str]
    user_initiation_prompt: str = dedent_triple_quote_str("""
        Please list captions for Tables that we can prepare for a scientific paper based on the \
        {outputs:data_analysis} (provided above).

        The captions that you choose should be returned as a Python Dict[str, str], with the keys \
        in the form of 'Table n' and the values being the actual captions of the tables.

        For example, you might return the following:
        ```python
        {
            'Table 1': 'Summary statistics of the dataset',
            'Table 2': 'Test for association of xxx with yyy (Linear Regression)',
            'Table 3': 'Factors affecting zzz and their interactions (Two Way ANOVA)',
        }
        ```

        Obviously, this is just an example. You should choose table captions that suit the information we have in \
        the output of the analysis code.

        Typically, a scientific paper has 2-3 tables, each containing completely unique and different results.
        You need to choose captions for a maximum of 1-4 tables that will each present distinct non-overlapping \
        information.

        Don't suggest captions that correspond to tables that are:
        * Not completely necessary.
        * Represent technical information, rather than scientific results.
        * Irrelevant to the research goal. 
        * Cannot be created solely from the code output.
        * Overlapping with other tables in your list. 

        Do not send any free text; Your response should be structured as a Python Dict[str, str].
        """)

    sentence_to_add_at_the_end_of_performer_response: str = dedent_triple_quote_str("""\n
        Please check the above chosen table captions, with specific attention to whether they \
        can be created solely from the code output above.

        If you find any issues, please provide bullet-point feedback.
        Or, if you are satisfied, please respond with "{termination_phrase}".

        Note you must either approve the table captions or provide feedback but not both.
        """)


@dataclass
class TablesReviewBackgroundProductsConverser(LatexReviewBackgroundProductsConverser,
                                              CheckExtractionReviewBackgroundProductsConverser):
    tolerance_for_too_wide_in_pts: Optional[float] = 25.0  # we allow tables to extend a bit out
    products: ScientificProducts = None
    max_reviewing_rounds: int = 0
    model_engine: ModelEngine = ModelEngine.GPT4
    background_product_fields: Tuple[str, ...] = ('data_file_descriptions',
                                                  'codes:data_analysis', 'outputs:data_analysis', 'research_goal',
                                                  'tables_and_tables_names')
    table_name: str = None
    product_fields_from_which_response_is_extracted: Tuple[str] = \
        ('data_file_descriptions', 'outputs:data_analysis',)
    conversation_name: str = 'tables'
    goal_noun: str = 'table for a scientific paper'
    goal_verb: str = 'produce'
    assistant_agent: ScientificAgent = ScientificAgent.Performer
    user_agent: ScientificAgent = ScientificAgent.TableExpert
    termination_phrase: str = 'The table does not require any enhancements'
    user_initiation_prompt: str = dedent_triple_quote_str("""
        Please build the table "{table_name}".
        Write the table in latex format, centered, in booktabs, multirow format.

        You should build the table using only results provided in the {outputs:data_analysis} above.

        As you build the Table, you should follow these guidelines (as applicable):

        (1) What to include in the table: 
        * Only include information that is relevant and suitable for inclusion in a table of a scientific paper.
        * There is absolutely no need to include all the information that is provided in the output.
        * Exclude rows/columns that are not important to the research goal, or that are too technical, \
        or that repeat the same information multiple times. 

        (2) What NOT to include in the table:
        * Do not include any presumed information that is not explicitly provided in the {outputs:data_analysis} above.
        * Do not leave any blank cells, or to-be-filled-later cells.

        (3) Table format and organization:
        * Organize the table sensibly, re-ordering rows/columns as appropriate.   
        * Rename technical names to scientifically-suitable names.
        * Rename technical values to scientifically-suitable values \
        (like values of 0/1 may be suitable to represent as "No"/"Yes").

        (4) Numeric values:
        * Round numbers to a reasonable number of digits, and present numbers using proper scientific notation.
        * Indicate standard errors using the $\\pm$ symbol, or parentheses.
        * If you indicate p-values, you can use the $<$ symbol to indicate smaller than a given value, \
        (any p-value less than 10^-4 should be indicated as $<$10^{-4}).

        (5) Table caption and label:
        * Add a caption suitable for inclusion as part of a scientific paper. \
        you can use the table name provided above, or modify it as you see fit.
        Use the format "\\caption{{Your chosen caption here}}".
        * Choose and add a table label in the format "\\label{{table:<your label here>}}".

        {do_not_repeat_information_from_previous_tables}

        """)

    sentence_to_add_at_the_end_of_performer_response: str = dedent_triple_quote_str("""
        Please provide actionable feedback on the above Table, with specific attention to whether the table \
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
    def do_not_repeat_information_from_previous_tables(self) -> str:
        if self.num_of_existing_tables > 0:
            return dedent_triple_quote_str("""
                Notice that the table should only add new information that is not included already \
                in the {} we already built (see above).
                """).format('table' if self.num_of_existing_tables == 1 else 'tables')
        else:
            return ''

    def _get_table_labels(self) -> List[str]:
        return [get_table_label(table) for table in self.products.tables['results']]

    def _check_table_label(self, section: str):
        label = get_table_label(section)
        if label is None:
            self._raise_self_response_error(r'Please add a label to the table. Use the format "\label{table:xxx}".')
        if not label.startswith('table:'):
            self._raise_self_response_error(r'The tabel label should start with "table:".')
        if label in self._get_table_labels():
            self._raise_self_response_error(f'The table label "{label}" is already used in another table.')

    def _process_non_math_parts(self, section: str) -> str:
        try:
            return escape_special_chars_and_symbols_in_table(section)
        except ValueError as e:
            self._raise_self_response_error(str(e))

    def _check_and_refine_section(self, section: str, section_name: str) -> str:
        section = super()._check_and_refine_section(section, section_name)
        self._check_extracted_numbers(section)
        self._check_table_label(section)
        return section


@dataclass
class KeyNumericalResultsExtractorReviewGPT(PythonDictReviewBackgroundProductsConverser,
                                            CheckExtractionReviewBackgroundProductsConverser):
    max_reviewing_rounds: int = 0
    background_product_fields: Tuple[str, ...] = ('research_goal', 'outputs:data_exploration', 'outputs:data_analysis',
                                                  'tables')
    product_fields_from_which_response_is_extracted: Tuple[str, ...] = (
        'outputs:data_exploration', 'outputs:data_analysis')
    ask_for_formula_prompt: str = None
    conversation_name: str = 'key_numerical_results_extractor'
    value_type: type = Dict[str, Any]
    goal_noun: str = 'key numerical values'
    goal_verb: str = 'extract'
    assistant_agent: ScientificAgent = ScientificAgent.Performer
    user_agent: ScientificAgent = ScientificAgent.InterpretationReviewer
    user_initiation_prompt: str = dedent_triple_quote_str("""
        Return a Python Dict[str, Any] of key numerical results we might need for a scientific paper.

        Considering the output files provided above \
        (see above "{outputs:data_exploration}" and "{outputs:data_analysis}"), \
        please identify key numerical results that are not represented in the latex tables above, but \
        that might still be needed for a scientific paper.

        These key numerical values should only include information that is explicitly extracted from the \
        output files provided above.
        The numerical results that you choose should be returned as a Python Dict[str, Any], \
        where the keys are the names \
        you choose for the results, and the values are the numerical results themselves.

        For example, if the analysis results provides a summary of a some statistical test, \
        you might include:

        ```python
        {
            'Total number of samples': xxx,
            'Accuracy of logistic regression for the XXX model': yyy,
            'AUC ROC of logistic regression for the XXX model': zzz,
        }
        ```

        Obviously, this is just an example. You should choose the numerical results that are most relevant \
        to the specific \
        results we got in the outputs and in light of the {research_goal} of the project as mentioned above.

        Be judicious when choosing values; a scientific paper will typically mention 3-10 important values.
        Do not send any free text! All descriptions should be included in the keys of the Python Dict[str, Any].
        """)
    sentence_to_add_at_the_end_of_performer_response: str = dedent_triple_quote_str("""
        Please provide feedback on the above {goal_noun}, with specific attention to whether they \
        contain only information that is explicitly extracted from the provided output data. Compare the numbers 
        in the provided Python dict values with the numbers in the result output data and explicitly mention \
        any discrepancies that need to get fixed.

        If you are satisfied, respond with "{termination_phrase}".
        """)

    def _extract_str_of_python_value_from_response(self, response: str) -> str:
        # we check the entire response to avoid cases that the response was not correctly formatted, yet included \
        # the correct flanking tags {} as part of a latex formula, rather than as part of a Python dict.
        self._check_extracted_numbers(response)
        return super()._extract_str_of_python_value_from_response(response)


@dataclass
class ResultsInterpretationReviewGPT(ScientificProductsQuotedReviewGPT):
    max_reviewing_rounds: int = 1
    background_product_fields: Tuple[str, ...] = ('data_file_descriptions', 'research_goal',
                                                  'tables', 'results_file')
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
