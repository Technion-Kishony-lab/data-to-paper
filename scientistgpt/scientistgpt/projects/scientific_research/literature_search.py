from dataclasses import dataclass
from typing import Tuple, Dict, Set, Iterable, List

from scientistgpt.base_steps import PythonValueReviewBackgroundProductsConverser, \
    PythonDictWithDefinedKeysReviewBackgroundProductsConverser
from scientistgpt.projects.scientific_research.cast import ScientificAgent
from scientistgpt.projects.scientific_research.scientific_products import LiteratureSearch
from scientistgpt.servers.semantic_scholar import SEMANTIC_SCHOLAR_SERVER_CALLER
from scientistgpt.utils import dedent_triple_quote_str, word_count
from scientistgpt.utils.nice_list import NiceDict, NiceList
from scientistgpt.utils.types import ListBasedSet


@dataclass
class GoalLiteratureSearchReviewGPT(PythonDictWithDefinedKeysReviewBackgroundProductsConverser):
    number_of_papers_per_query: int = 7
    max_reviewing_rounds: int = 0
    requested_keys: Iterable[str] = ('dataset', 'questions', )
    background_product_fields: Tuple[str, ...] = ('research_goal', 'hypothesis_testing_plan')
    conversation_name: str = 'literature_search_goal'
    is_new_conversation: bool = None
    value_type: type = Dict[str, List[str]]
    goal_noun: str = 'literature search queries'
    goal_verb: str = 'write'
    assistant_agent: ScientificAgent = ScientificAgent.Performer
    user_agent: ScientificAgent = ScientificAgent.CitationExpert
    user_initiation_prompt: str = dedent_triple_quote_str("""
        Please write literature-search queries that we can use to search for papers related to our study.
        
        You would need to compose search queries to identify prior papers covering these 2 areas:
        
        "dataset": papers that use the same or similar datasets as in our study
        "questions": papers that ask questions similar to our study

        Return your answer as a `Dict[str, List[str]]`, where the keys are the 2 areas noted above, \
        and the values are lists of query string. Each individual query should be a string with up to 5-10 words. 
        
        For example, for a study reporting waning of the efficacy of the covid-19 BNT162b2 vaccine based on analysis \
        of the real-world UK National Core dataset, the queries could be:  
        {
            "dataset": ["covid-19 vaccine real-world data", "The UK National Core covid-19 dataset"]
            "questions": ["covid-19 vaccine efficacy", "covid-19 vaccine efficacy over time", "covid-19 vaccine waning"]
        }
        """)

    def _check_response_value(self, response_value: dict) -> NiceDict:
        for queries in response_value.values():
            for query in queries:
                if word_count(query) > 10:
                    self._raise_self_response_error('queries should be 5-10 word long')
        return NiceDict({k: NiceList(v, wrap_with='"', prefix='[\n' + ' ' * 8, suffix='\n' + ' ' * 4 + ']',
                                     separator=',\n' + ' ' * 8)
                         for k, v in response_value.items()})

    def get_literature_search(self) -> LiteratureSearch:
        scopes_to_list_of_queries = self.run_dialog_and_get_valid_result()
        literature_search = LiteratureSearch()
        for scope, queries in scopes_to_list_of_queries.items():
            queries_to_citations = {}
            for query in queries:
                queries_to_citations[query] = \
                    SEMANTIC_SCHOLAR_SERVER_CALLER.get_server_response(query, rows=self.number_of_papers_per_query)
            literature_search.scopes_to_queries_to_citations[scope] = queries_to_citations
        return literature_search


@dataclass
class WritingLiteratureSearchReviewGPT(GoalLiteratureSearchReviewGPT):
    requested_keys: Iterable[str] = ('background', 'dataset', 'methods', 'questions', 'results')
    background_product_fields: Tuple[str, ...] = ('research_goal', 'hypothesis_testing_plan', 'title_and_abstract')
    conversation_name: str = 'literature_search_writing'
    user_initiation_prompt: str = dedent_triple_quote_str("""
        Please write literature-search queries that we can use to search for papers related to our study.

        You would need to compose search queries to identify prior papers covering these 5 areas:

        "background": papers that provide background on the overall subject of our study
        "dataset": papers that use the same or similar datasets as in our study
        "methods": papers that use the same or similar methods as in our study
        "questions": papers that ask questions similar to our study
        "results": papers reporting results similar or related to our results

        Return your answer as a `Dict[str, List[str]]`, where the keys are the 5 areas noted above, \
        and the values are lists of query string. Each individual query should be a string with up to 5-10 words. 

        For example, for a study reporting waning of the efficacy of the covid-19 BNT162b2 vaccine based on analysis \
        of the real-world UK National Core dataset, the queries could be:  
        {
            "background": ["SARS-CoV2 spread", "covid-19 global impact", "covid-19 vaccine"]
            "dataset": ["covid-19 vaccine real-world data", "The UK National Core covid-19 dataset"]
            "methods": ["covid-19 vaccine efficacy analysis", "kaplan-meier survival analysis"]
            "questions": ["covid-19 vaccine efficacy", "covid-19 vaccine efficacy over time"]
            "results": ["covid-19 vaccine efficacy waning"]
        }
        """)
