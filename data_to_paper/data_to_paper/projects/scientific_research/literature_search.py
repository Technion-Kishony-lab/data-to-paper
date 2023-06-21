from dataclasses import dataclass
from typing import Tuple, Dict, Iterable, List

import numpy as np

from data_to_paper.base_steps import PythonDictWithDefinedKeysReviewBackgroundProductsConverser
from data_to_paper.projects.scientific_research.cast import ScientificAgent
from data_to_paper.projects.scientific_research.scientific_products import LiteratureSearch, ScientificProducts
from data_to_paper.servers.semantic_scholar import SEMANTIC_SCHOLAR_SERVER_CALLER, \
    SEMANTIC_SCHOLAR_EMBEDDING_SERVER_CALLER
from data_to_paper.utils import dedent_triple_quote_str, word_count
from data_to_paper.utils.nice_list import NiceDict, NiceList


@dataclass
class GoalLiteratureSearchReviewGPT(PythonDictWithDefinedKeysReviewBackgroundProductsConverser):
    products: ScientificProducts = None
    number_of_papers_per_scope: int = 7
    max_reviewing_rounds: int = 0
    requested_keys: Iterable[str] = ('dataset', 'questions', )
    background_product_fields: Tuple[str, ...] = ('data_file_descriptions', 'research_goal', 'hypothesis_testing_plan')
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
        of the "United Kingdom National Core Data (UK-NCD)", the queries could be:  
        {
            "dataset": ["The UK-NCD dataset", "covid-19 vaccine efficacy dataset"]
            "questions": ["covid-19 vaccine efficacy over time", "covid-19 vaccine waning"]
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

    def get_literature_search(self, rows: int = None) -> LiteratureSearch:
        scopes_to_list_of_queries = self.run_dialog_and_get_valid_result()
        literature_search = LiteratureSearch()
        for scope, queries in scopes_to_list_of_queries.items():
            queries_to_citations = {}
            num_queries = len(queries)
            number_of_papers_per_query = self.number_of_papers_per_scope // num_queries + 1 if rows is None else rows
            for query in queries:
                citations = SEMANTIC_SCHOLAR_SERVER_CALLER.get_server_response(query, rows=number_of_papers_per_query)
                self.comment(f'\nQuerying Semantic Scholar for {number_of_papers_per_query} citations, for: '
                             f'"{query}".\nFound {len(citations)} citations:\n{citations}')
                queries_to_citations[query] = citations

            literature_search.scopes_to_queries_to_citations[scope] = queries_to_citations
        return literature_search


@dataclass
class WritingLiteratureSearchReviewGPT(GoalLiteratureSearchReviewGPT):
    requested_keys: Iterable[str] = ('background', 'dataset', 'methods', 'results')
    background_product_fields: Tuple[str, ...] = ('data_file_descriptions', 'research_goal', 'hypothesis_testing_plan',
                                                  'title_and_abstract')
    conversation_name: str = 'literature_search_writing'
    user_initiation_prompt: str = dedent_triple_quote_str("""
        Please write literature-search queries that we can use to search for papers related to our study.

        You would need to compose search queries to identify prior papers covering these 4 areas:

        "background": papers that provide background on the overall subject of our study
        "dataset": papers that use the same or similar datasets as in our study
        "methods": papers that use the same or similar methods as in our study
        "results": papers asking similar questions to our results

        Return your answer as a `Dict[str, List[str]]`, where the keys are the 5 areas noted above, \
        and the values are lists of query string. Each individual query should be a string with up to 5-10 words. 

        For example, for a study reporting waning of the efficacy of the covid-19 BNT162b2 vaccine based on analysis \
        of the "United Kingdom National Core Data (UK-NCD)", the queries could be:  
        {
            "background": ["SARS-CoV2 spread", "covid-19 global impact", "covid-19 vaccine"]
            "dataset": ["The UK-NCD dataset", "covid-19 vaccine efficacy dataset"]
            "methods": ["covid-19 vaccine efficacy analysis", "kaplan-meier survival analysis"]
            "results": ["covid-19 vaccine efficacy", "covid-19 vaccine efficacy over time", \
            "covid-19 vaccine efficacy waning"]
        }
        """)

    def get_literature_search(self, rows: int = None) -> LiteratureSearch:
        literature_search = super().get_literature_search(rows=100)
        literature_search.embedding_target = \
            SEMANTIC_SCHOLAR_EMBEDDING_SERVER_CALLER.get_server_response({
                "paper_id": "",
                "title": self.products.get_title(),
                "abstract": self.products.get_abstract()})
        return literature_search
