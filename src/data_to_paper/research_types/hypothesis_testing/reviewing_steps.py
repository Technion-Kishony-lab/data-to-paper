import re
from dataclasses import dataclass, field
from typing import Tuple, Dict, Any, Iterable, List, Collection, Type

from data_to_paper.env import JSON_MODE, WRITING_MODEL_ENGINE
from data_to_paper.servers.model_engine import ModelEngine
from data_to_paper.text import dedent_triple_quote_str, word_count
from data_to_paper.base_steps.result_converser import Rewind
from data_to_paper.base_steps import BaseProductsQuotedReviewGPT, PythonDictReviewBackgroundProductsConverser, \
    PythonDictWithDefinedKeysReviewBackgroundProductsConverser
from data_to_paper.base_products.product import ValueProduct

from data_to_paper.servers.custom_types import Citation

from .cast import ScientificAgent
from .product_types import GoalAndHypothesisProduct, MostSimilarPapersProduct, NoveltyAssessmentProduct, \
    HypothesisTestingPlanProduct
from .scientific_products import ScientificProducts
from .writing_steps import ShowCitationProducts


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
    model_engine: ModelEngine = WRITING_MODEL_ENGINE
    LLM_PARAMETERS = {'temperature': 1.0}
    max_reviewing_rounds: int = 1
    background_product_fields: Tuple[str, ...] = ('data_file_descriptions_no_headers',
                                                  'codes_and_outputs:data_exploration')
    conversation_name: str = 'Research Goal'
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
        based on the provided headers of our data files (see "{data_file_descriptions_no_headers}", above).

        {project_specific_goal_guidelines}\t
        * Do not suggest methodology. Just the goal and an hypothesis. 
        """)
    mission_prompt: str = dedent_triple_quote_str("""\n
        Please suggest a research goal and an hypothesis that can be studied using only the provided dataset. 
        The goal and hypothesis should be interesting and novel.
        {goal_guidelines}

        Your response should be formatted as {your_response_should_be_formatted_as}
        """)
    your_response_should_be_formatted_as: str = dedent_triple_quote_str("""
        a triple-backtick block, like this:
        ```
        # Research Goal: 
        <your research goal here>

        # Hypothesis: 
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

    product_type: Type[ValueProduct] = GoalAndHypothesisProduct

    def _check_extracted_text_and_update_valid_result(self, extracted_text: str):
        if '\n# Research Goal:' not in extracted_text or '\n# Hypothesis:' not in extracted_text:
            self._raise_self_response_error(
                title='# Incorrect response format',
                error_message='Your response should contain both a "# Research Goal:" and a "# Hypothesis:" section.',
            )
        self._update_valid_result(extracted_text)


@dataclass
class GetMostSimilarCitations(ShowCitationProducts, PythonDictReviewBackgroundProductsConverser):
    json_mode: bool = JSON_MODE
    products: ScientificProducts = None
    allow_citations_from_step: str = 'goal'
    max_reviewing_rounds: int = 0

    value_type: type = Dict[str, str]
    goal_noun: str = 'most similar papers'
    goal_verb: str = 'find'
    assistant_agent: ScientificAgent = ScientificAgent.Performer
    user_agent: ScientificAgent = ScientificAgent.GoalReviewer
    conversation_name: str = 'Identify Similar Publications'
    is_new_conversation: bool = None  # this will create "similar_citations_0", etc.
    background_product_fields: Tuple[str, ...] = ('data_file_descriptions_no_headers', 'research_goal',
                                                  'literature_search:goal:dataset', 'literature_search:goal:questions')

    mission_prompt: str = dedent_triple_quote_str("""
        From the literature search above, list up to 5 key papers whose results are most \t
        similar/overlapping with our research goal and hypothesis.

        Return your response as a {python_or_json} Dict[str, str], where the keys are bibtex ids of the papers, \t
        and the values are the titles of the papers. For example:

        ```{python_or_json}
        {
            "Smith2020TheAB": 
                "A title of a paper most overlapping with our goal and hypothesis",
            "Jones2021AssortedCD": 
                "Another title of a paper that is similar to our goal and hypothesis",
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
            self._raise_self_response_error(
                title='Invalid bibtex ids',
                error_message=f'Invalid bibtex ids:\n{non_matching_ids}')

        # replace with correct citation titles
        response_value = type(response_value)({key: bibtex_ids_to_citations[key].title for key in response_value})
        return response_value

    def _get_overlapping_citations(self, ids_to_titles: Dict[str, str]) -> List[Citation]:
        available_citations = self._get_available_citations()
        return [citation for citation in available_citations if citation.bibtex_id in ids_to_titles]

    def _convert_valid_result_to_product(self, valid_result: Dict[str, str]) -> MostSimilarPapersProduct:
        return MostSimilarPapersProduct(value=self._get_overlapping_citations(valid_result))

    def _convert_product_back_to_valid_result(self, product: MostSimilarPapersProduct) -> Dict[str, str]:
        return {citation.bibtex_id: citation.title for citation in product}


@dataclass
class NoveltyAssessmentReview(ShowCitationProducts, PythonDictWithDefinedKeysReviewBackgroundProductsConverser):
    json_mode: bool = JSON_MODE
    products: ScientificProducts = None
    value_type: type = Dict[str, Any]
    allowed_values_for_keys: Dict[str, Iterable] = field(default_factory=lambda: {'choice': ('OK', 'REVISE')})
    default_rewind_for_result_error: Rewind = Rewind.AS_FRESH_CORRECTION  # to maintain chain of thought
    goal_noun: str = 'novelty assessment'
    goal_verb: str = 'check'
    assistant_agent: ScientificAgent = ScientificAgent.Performer
    user_agent: ScientificAgent = ScientificAgent.GoalReviewer
    conversation_name: str = 'Assess Goal Novelty'
    requested_keys: Collection[str] = ('similarities', 'differences', 'choice', 'explanation')
    is_new_conversation: bool = None  # this will create "research_goal_0", etc.
    background_product_fields: Tuple[str, ...] = ('general_dataset_description', 'research_goal',
                                                  'most_similar_papers')
    sentence_to_add_at_the_end_of_reviewer_response: str = dedent_triple_quote_str("""
        Please correct your {goal_noun} based on the feedback provided.
        Make sure to return your full assessment, as {your_response_should_be_formatted_as}.
        """)

    mission_prompt: str = dedent_triple_quote_str("""
        We would like to assess the novelty of our {research_goal} with respect to the literature.
        Given the related papers listed above, please return \t
        {your_response_should_be_formatted_as}. Where:

        * "similarities": Provide a List[str] of potential similarities between our goal and hypothesis, \t
        and the related papers listed above.

        * "differences": Provide a List[str] of potential differences, if any, between our stated {research_goal} \t
        and the related papers listed above.

        * "choice": Given your assessment above, choose one of the following two options:

        a. Our goal and hypothesis offer a significant novelty compared to existing literature, and \t
        will likely lead to interesting and novel findings {"choice": "OK"}.

        b. Our goal and hypothesis have overlap with existing literature, and I can suggest ways to \t
        revise them to make them more novel {"choice": "REVISE"}.

        * "explanation": Provide a brief explanation of your choice.

        For example:

        ```{python_or_json}
        {
            "similarities": [
                "Our research goal is similar to the paper by ... in that ...",
                "Our research goal somewhat overlaps with the findings of ...",
                "Our hypothesis is similar to the paper by ... in that ..."
            ],
            "differences": [
                "Our goal and hypothesis are distinct because ...",
                "Our hypothesis differs from the paper by ... in that ..."
            ],

            "choice": "OK",
            "explanation": "While our goal and hypothesis have some overlap with existing literature, \t
        I believe that the ... aspect of our research is novel and will lead to ..."

            # or:

            "choice": "REVISE"
            "explanation": "The overlap with the result of ... is too significant, and I think we can \t
        revise our goal to make it more novel, for example by ..."
        }
        ```
        """)

    your_response_should_be_formatted_as: str = dedent_triple_quote_str("""
        a {python_or_json} dictionary, like this:"
        {"similarities": List[str], "differences": List[str], "choice": str, "explanation": str}
        """)

    product_type: Type[ValueProduct] = NoveltyAssessmentProduct

    def _check_response_value(self, response_value: Any) -> Any:
        response_value = super()._check_response_value(response_value)
        errors = []
        if response_value["choice"] not in ["OK", "REVISE"]:
            errors.append(f'Invalid choice: {response_value["choice"]}. Choose "OK" or "REVISE".')
        if not isinstance(response_value["explanation"], str):
            errors.append(f"Explanation must be a string.")
        for key in ["similarities", "differences"]:
            if not isinstance(response_value[key], list):
                errors.append(f'"{key}" must be a list of strings.')
            for item in response_value[key]:
                if not isinstance(item, str):
                    errors.append(f'Each item in "{key}" must be a string.')
        if errors:
            errors = '\n'.join(errors)
            self._raise_self_response_error(
                title='# Errors in response structure',
                error_message=errors,
            )
        return response_value


@dataclass
class ReGoalReviewGPT(GoalReviewGPT):
    is_new_conversation: bool = None
    max_reviewing_rounds: int = 0
    background_product_fields: Tuple[str, ...] = ('data_file_descriptions_no_headers',
                                                  'codes_and_outputs:data_exploration',
                                                  'research_goal', 'most_similar_papers')
    mission_prompt: str = dedent_triple_quote_str("""
        Based on the result of the literature search above, \t
        please revise, or completely re-write, the research goal and hypothesis that we have so that they \t
        do not completely overlap existing literature.
        {goal_guidelines}

        Your response should be formatted as {your_response_should_be_formatted_as}
        """)


@dataclass
class HypothesesTestingPlanReviewGPT(PythonDictWithDefinedKeysReviewBackgroundProductsConverser):
    json_mode: bool = JSON_MODE
    value_type: type = Dict[str, Dict[str, str]]
    requested_keys: Collection[str] = ('ISSUES', 'HYPOTHESES')
    max_valid_response_iterations: int = 4
    max_hypothesis_count: int = 3
    max_reviewing_rounds: int = 0  # 0 for no review cycles
    default_rewind_for_result_error: Rewind = Rewind.AS_FRESH_CORRECTION  # to maintain chain of thought
    background_product_fields: Tuple[str, ...] = ('data_file_descriptions_no_headers',
                                                  'codes_and_outputs:data_exploration',
                                                  'research_goal')
    your_response_should_be_formatted_as: str = dedent_triple_quote_str("""
        a {python_or_json} dictionary with the following structure:
        ```{python_or_json}
        {
            "ISSUES": {
                "<Issue>": "<Description of the issue and how it should be accounted for>",
                "<Another issue>": "...",
                "etc": "..."
            }

            "HYPOTHESES": {
                "<Hypothesis>": "<Statistical test>",
                "<another Hypothesis>": "...",
                "etc": "..."
            }
        }
        ```
        """)
    conversation_name: str = 'Hypothesis Testing Plan'
    is_new_conversation: bool = None  # this will create "hyp_testing_plan_0", etc.
    goal_noun: str = 'hypothesis testing plan'
    goal_verb: str = 'write'
    mission_prompt: str = dedent_triple_quote_str("""
        We would like to test the specified hypotheses using the provided dataset.
        We need to think of the relevant statistical issues and the most adequate statistical tests for each hypothesis.

        Review the "{data_file_descriptions_no_headers}" and "{codes_and_outputs:data_exploration}" provided above, \t
        and return your assessment as {your_response_should_be_formatted_as}

        - ISSUES:
        The keys of this dictionary should briefly describe the statistical issues that we should account for.
        The values should describe the issue and how it should be accounted for in the statistical tests.
        For possible issues (keys), consider for example:
        * Confounding variables (see available variables in the dataset that we can adjust for).
        * Missing data points.
        * Dependencies between data points.
        * Multiple comparisons.
        * Imbalanced data.
        * Any other relevant statistical issues.

        - HYPOTHESES
        The keys of this dictionary should briefly describe each of our hypotheses.
        The values of this dictionary \t
        should specify the most adequate statistical test for each hypothesis, \t
        and describe how it should be performed while accounting for any issues you have outlined above.

        For each of our hypotheses, suggest a *single* statistical test.
        If there are several possible ways to test a given hypothesis, specify only *one* statistical test \t
        (the simplest one).

        Example:

        ```{python_or_json}
        {
            "ISSUES": {
                "Missing data points": 
                    "Based on the {codes_and_outputs:data_exploration}, \t
        we should drop lines with missing data in ...",
                "Confounding variables": 
                    "We should adjust for ..."
            },
            "HYPOTHESES": {
                "xxx is associated with yyy and zzz":
                    "Linear regression with xxx as the independent variable and \t
        yyy and zzz as the dependent variables while adjusting for aaa, bbb, ccc",
                "The association between xxx and yyy is moderated by zzz": 
                    "Repeat the above linear regression, while adding the interaction term between yyy and zzz"
        }
        ```

        These of course are just examples. Your actual response should be based on the \t
        "{research_goal}", "{data_file_descriptions_no_headers}", and "{codes_and_outputs:data_exploration}".

        Note how in the example shown the different hypotheses are connected to each other, building towards a single
        study goal.

        Remember to return a valid {python_or_json} dictionary with the structure described above.
        """)
    assistant_agent: ScientificAgent = ScientificAgent.Performer
    user_agent: ScientificAgent = ScientificAgent.PlanReviewer
    product_type: Type[ValueProduct] = HypothesisTestingPlanProduct

    def _check_response_value(self, response_value: Any) -> Any:
        """
        Strip "hypothesis x" from the keys of the response value.
        """
        response_value = super()._check_response_value(response_value)

        # what we have is "usable" at this point:
        self._update_valid_result(response_value)

        hypotheses = response_value['HYPOTHESES']

        if len(hypotheses) > self.max_hypothesis_count:
            self._raise_self_response_error(
                title='# Too many hypotheses',
                error_message=dedent_triple_quote_str(f"""
                    Please do not specify more than {self.max_hypothesis_count} hypotheses.
                    Revise your response to return a maximum of {self.max_hypothesis_count} hypotheses, \t
                    which should all build towards a single study goal.
                    """)
            )

        if not hypotheses:
            self._raise_self_response_error(
                title='# No hypotheses',
                error_message='Please specify at least one hypothesis.'
            )

        # We want explicit hypotheses. Check that the hypotheses have at least 7 words:
        for hypothesis, test in hypotheses.items():
            if word_count(hypothesis) < 5:
                self._raise_self_response_error(
                    title='# Hypothesis too short',
                    error_message=f'The hypothesis "{hypothesis}" is too short.\n'
                                  f'Please provide a more explicit and specific hypothesis description.'
                )
            if word_count(test) < 12:
                self._raise_self_response_error(
                    title='# Hypothesis test too short',
                    error_message=f'The test description "{test}" is too short.\n'
                                  f'Please provide a more explicit and specific test description.'
                )

        # remove "hypothesis x" from the keys (we don't want the hypotheses to be numbered)
        hypotheses = type(hypotheses)(
            {re.sub(pattern=r'hypothesis \d+:|hypothesis:|hypothesis :',
                    repl='', string=k, flags=re.IGNORECASE).strip(): v
             for k, v in hypotheses.items()})
        response_value['HYPOTHESES'] = hypotheses
        return response_value
