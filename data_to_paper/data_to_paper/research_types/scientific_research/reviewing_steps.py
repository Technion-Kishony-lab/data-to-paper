import pickle
import re
from dataclasses import dataclass, field
from typing import Tuple, Dict, Any, Iterable, List

from data_to_paper.servers.model_engine import ModelEngine
from data_to_paper.utils import dedent_triple_quote_str
from data_to_paper.base_steps.result_converser import Rewind
from data_to_paper.base_steps import BaseProductsQuotedReviewGPT, PythonDictReviewBackgroundProductsConverser, \
    PythonDictWithDefinedKeysAndValuesReviewBackgroundProductsConverser

from data_to_paper.servers.custom_types import Citation

from .cast import ScientificAgent
from .scientific_products import ScientificProducts
from .writing_steps import ShowCitationProducts
from .model_engines import get_model_engine_for_class
from ...utils.file_utils import run_in_directory


@dataclass
class ScientificProductsQuotedReviewGPT(BaseProductsQuotedReviewGPT):

    sentence_to_add_at_the_end_of_performer_response: str = dedent_triple_quote_str("""
        Please provide feedback on the above {goal_noun}, with specific attention to whether it can be \t
        studied using only the provided dataset, without requiring any additional data \t
        (pay attention to using only data explicitly available in the provided headers of our data files \t
        as described in our dataset, above).
        Do not suggest changes to the {goal_noun} that may require data not available in our dataset.
        If you are satisfied, respond with "{termination_phrase}".
        """)


@dataclass
class GoalReviewGPT(ScientificProductsQuotedReviewGPT):
    CHATGPT_PARAMETERS = {'temperature': 1.0}
    max_reviewing_rounds: int = 1
    background_product_fields: Tuple[str, ...] = ('data_file_descriptions_no_headers',
                                                  'codes_and_outputs:data_exploration')
    conversation_name: str = 'research_goal'
    other_conversation_name: str = 'research_goal_reviewer'
    goal_noun: str = 'research goal and hypothesis'
    goal_verb: str = 'suggest'
    assistant_agent: ScientificAgent = ScientificAgent.Performer
    user_agent: ScientificAgent = ScientificAgent.GoalReviewer
    termination_phrase: str = \
        'The research goal does not require any changes'

    project_specific_goal_guidelines: str = ""
    goal_guidelines: str = dedent_triple_quote_str("""\n
        Guidelines:

        * Try to avoid trivial hypotheses (like just testing for simple linear associations).
        Instead, you could perhaps explore more complex associations and relationships, like testing for \t
        moderation effects or interactions between variables.

        * Do not limit yourself to the provided data structure and variables; \t
        you can create new variables from the existing ones, and use them in your hypotheses.

        * Make sure that your suggested hypothesis can be studied using only the provided dataset, \t
        without requiring any additional data. In particular, pay attention to using only data available \t
        based on the provided headers of our data files (see "{data_file_descriptions}", above).

        {project_specific_goal_guidelines}\t
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
        * If the hypothesis cannot be tested using only the provided dataset (without \t
        requiring additional data), suggest how to modify the hypothesis to better fit the dataset.
        * If the hypothesis is not interesting and novel, suggest how to modify it to make it more interesting.
        * If the hypothesis is broad or convoluted, suggest how best to focus it on a single well defined question.


        Do not provide positive feedback; if these conditions are all satisfied, just respond with: 
        "{termination_phrase}".
        If you feel that the initial goal and hypothesis satisfy the above conditions, \t
        respond solely with "{termination_phrase}".
    """)


@dataclass
class GetMostSimilarCitations(ShowCitationProducts, PythonDictReviewBackgroundProductsConverser):
    products: ScientificProducts = None
    allow_citations_from_step: str = 'goal'
    max_reviewing_rounds: int = 0

    model_engine: ModelEngine = field(default_factory=lambda: get_model_engine_for_class(GetMostSimilarCitations))
    value_type: type = Dict[str, str]
    goal_noun: str = 'most similar papers'
    goal_verb: str = 'find'
    assistant_agent: ScientificAgent = ScientificAgent.Performer
    user_agent: ScientificAgent = ScientificAgent.GoalReviewer
    conversation_name: str = 'similar_citations'
    is_new_conversation: bool = None  # this will create "similar_citations_0", etc.
    background_product_fields: Tuple[str, ...] = ('data_file_descriptions_no_headers', 'research_goal',
                                                  'literature_search:goal:dataset', 'literature_search:goal:questions')

    user_initiation_prompt: str = dedent_triple_quote_str("""
        From the literature search above, list up to 5 key papers whose results are most \t
        similar/overlapping with our research goal and hypothesis.

        Return your response as a Python Dict[str, str], where the keys are bibtex ids of the papers, \t
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
    model_engine: ModelEngine = field(default_factory=lambda: get_model_engine_for_class(IsGoalOK))
    value_type: type = Dict[str, str]
    allowed_values_for_keys: Dict[str, Iterable] = field(default_factory=lambda: {'choice': ('OK', 'REVISE')})
    default_rewind_for_result_error: Rewind = Rewind.AS_FRESH_CORRECTION  # to maintain chain of thought
    goal_noun: str = 'research goal and hypothesis'
    goal_verb: str = 'check'
    assistant_agent: ScientificAgent = ScientificAgent.Performer
    user_agent: ScientificAgent = ScientificAgent.GoalReviewer
    conversation_name: str = 'is_goal_ok'
    is_new_conversation: bool = None  # this will create "research_goal_0", etc.
    background_product_fields: Tuple[str, ...] = ('general_dataset_description', 'research_goal',
                                                  'literature_search:goal:goal and hypothesis')

    user_initiation_prompt: str = dedent_triple_quote_str("""
        Given the related papers listed above, please follow these 3 steps:

        (1) Provide a bullet-point list of potential similarities between our goal and hypothesis, \t
        and the related papers listed above.

        (2) Determine in what ways, if any, our stated goal and hypothesis are distinct from the related papers \t
        listed above.

        (3) Given your assessment above, choose one of the following two options:

        a. Our goal and hypothesis offer a significant novelty compared to existing literature, and \t
        will likely lead to interesting and novel findings {'choice': 'OK'}.

        b. Our goal and hypothesis have overlap with existing literature, and I can suggest ways to \t
        revise them to make them more novel {'choice': 'REVISE'}.

        Your response for this part should be formatted as a Python dictionary mapping 'choice' to \t
        either 'OK' or 'REVISE'. 
        Namely, return either: {'choice': 'OK'} or {'choice': 'REVISE'}
        """)

    def is_goal_ok(self):
        return self.run_and_get_valid_result()['choice'] == 'OK'


@dataclass
class ReGoalReviewGPT(GoalReviewGPT):
    is_new_conversation: bool = None
    max_reviewing_rounds: int = 0
    background_product_fields: Tuple[str, ...] = ('data_file_descriptions_no_headers',
                                                  'codes_and_outputs:data_exploration',
                                                  'research_goal', 'literature_search:goal:goal and hypothesis')
    user_initiation_prompt: str = dedent_triple_quote_str("""
        Based on the result of the literature search above, \t
        please revise, or completely re-write, the research goal and hypothesis that we have so that they \t
        do not completely overlap existing literature.
        {goal_guidelines}
        {quote_request}
        """)


@dataclass
class HypothesesTestingPlanReviewGPT(PythonDictReviewBackgroundProductsConverser):
    value_type: type = Dict[str, str]
    max_valid_response_iterations: int = 4
    max_hypothesis_count: int = 3
    max_reviewing_rounds: int = 0  # 0 for no review cycles
    default_rewind_for_result_error: Rewind = Rewind.AS_FRESH_CORRECTION  # to maintain chain of thought
    background_product_fields: Tuple[str, ...] = ('data_file_descriptions_no_headers',
                                                  'codes_and_outputs:data_exploration',
                                                  'research_goal')
    conversation_name: str = 'hypothesis_testing_plan'
    is_new_conversation: bool = None  # this will create "hyp_testing_plan_0", etc.
    goal_noun: str = 'hypothesis testing plan'
    goal_verb: str = 'write'
    user_initiation_prompt: str = dedent_triple_quote_str("""
        We would like to test the specified hypotheses using the provided dataset.

        Please follow these two steps:

        (1) Return a bullet-point review of relevant statistical issues.
        Read the "{data_file_descriptions}" and the "{codes_and_outputs:data_exploration}" provided above, \t
        and then for each of the following generic \t
        statistical issues determine if they are relevant for our case and whether they should be accounted for: 
        * multiple comparisons.
        * confounding variables (see available variables in the dataset that we can adjust for).
        * dependencies between data points.
        * missing data points.
        * any other relevant statistical issues.

        (2) Create a Python Dict[str, str], mapping each hypothesis (dict key) to the statistical test that \t
        would be most adequate for testing it (dict value).
        The keys of this dictionary should briefly describe each of our hypotheses.
        The values of this dictionary should specify the most adequate statistical test for each hypothesis, \t
        and describe how it should be performed while accounting for any issues you have outlined above as relevant.

        For each of our hypotheses, suggest a *single* statistical test.
        If there are several possible ways to test a given hypothesis, specify only *one* statistical test \t
        (the simplest one).

        Your response for this part should be formatted as a Python dictionary, like this:
        ```python
        {
            "xxx is associated with yyy and zzz":
                "linear regression with xxx as the independent variable and \t
        yyy and zzz as the dependent variables while adjusting for aaa, bbb, ccc",
            "the association between xxx and yyy is moderated by zzz": 
                "repeat the above linear regression, \t
        while adding the interaction term between yyy and zzz",
        }
        ```

        These of course are just examples. Your actual response should be based on the goal and hypotheses that \t
        we have specified above (see the "{research_goal}" above).

        Note how in the example shown the different hypotheses are connected to each other, building towards a single
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
class ReflectOnAnalysisGPT(PythonDictWithDefinedKeysAndValuesReviewBackgroundProductsConverser):
    products: ScientificProducts = None
    model_engine: ModelEngine = field(default_factory=lambda: get_model_engine_for_class(ReflectOnAnalysisGPT))
    value_type: type = Dict[str, int]
    allowed_values_for_keys: Dict[str, Iterable] = field(default_factory=lambda:
    {'simplicity': range(1, 11),
     'clarity': range(1, 11),
     'adequate_hypothesis':range(1, 11),
     'adequate_data': range(1, 11),
     'error_free': range(1, 11)})
    default_rewind_for_result_error: Rewind = Rewind.AS_FRESH_CORRECTION  # to maintain chain of thought
    goal_noun: str = 'qualities and correctness of the analysis'
    goal_verb: str = 'reflect'
    assistant_agent: ScientificAgent = ScientificAgent.Performer
    user_agent: ScientificAgent = ScientificAgent.AnalysisReviewer
    conversation_name: str = 'reflect_on_analysis'
    is_new_conversation: bool = None
    background_product_fields: Tuple[str, ...] = ('general_dataset_description', 'data_file_descriptions_no_headers',
                                                  'hypothesis_testing_plan', 'codes:data_analysis')

    user_initiation_prompt: str = dedent_triple_quote_str("""
        Based on the data description, the hypothesis testing plan, and the data analysis code, evaluate the \t
        following 5 criteria of the task at hand and the provided code:
        
        - Simplicity: How complex is the task? Very simple tasks (10) correspond to single regression analysis or \t
        similar, while very complex tasks (1) require several analysis steps, such as the generation of new \t
        data columns, complicated data analysis functions such as machine learning models and/or complex data input \t
        files, such as non-tabular data.
        
        - Clarity: How readable and understandable is the code? In very clear code (10), all variables have \t
        non-ambiguous names and all data transformations are easy to follow. Further, code comments are helpful and \t
        also non-ambiguous. Unclear codes (1) contain, for example, convoluted data operations, such as for loops and \t
        unclear variable naming, and no or limited code comments.
        
        - Adequate code for hypothesis testing plan: How well does the data analysis code align with the hypothesis \t
        testing plan? A very adequate code (10) performs all analyses that are specified in the \t
        hypothesis testing plan, but not any other analysis, while an inadequate code (1) performs only analyses \t
        which are not specified in the hypothesis testing plan.
        
        - Adequate code for data features: How adequate is the code in light of the data features? Are all relevant \t
        data features used in the code, while not relevant information is not included? Are the data features which \t
        are used in the analysis reflect what they stand for? For example, an adequate code (10) includes all \t
        relevant confounding factors, while inadequate code leaves out relevant data features and uses far \t
        fetched proxies, for example using economic status as a proxy for happiness. As part of this reflection, list \t
        all the variables that are requested to be tested in the hypothesis testing plan and their corresponding \t
        counterpart in the code, and vice versa - list all the variables in the code and their corresponding \t
        counterpart in the hypothesis testing plan. If there exists a mismatch, the score corresponds to (1).
        
        - Error free: Is there any error in the code? For example, are all the mathematical formulas, if applicable, \t
        correct? Do variables correspond to the respective output? If the code is error free, evaluate it with 10. \t
        If there are major errors, such as errors in formulas, it corresponds to 1.
        
        Your response should start with a reflection on the relevant points for each criterion, this reflection should
        include examples from the provided scientific products and be very thorough. It should conclude with a \t
        final score from 1 to 10 representing a summary of the reflection. 
        
        At the end of your response you should provide a final verdict, it should be formatted as a Python dictionary \t
        mapping each of the 5 criteria: ['simplicity','clarity','adequate_hypothesis','adequate_data','error_free'] \t
        to a score from 1 to 10. 
        For example, it may look as something like that:
        {'simplicity': 1,
        'clarity': 7,
        'adequate_hypothesis': 4,
        'adequate_data': 5,
        'error_free': 8}
        """)

    def save_reflection(self):
        with run_in_directory(self.output_directory):
            with open('reflection_on_analysis.pkl', 'wb') as f:
                pickle.dump(self.run_and_get_valid_result(), f)
