from dataclasses import dataclass, field
from typing import Dict, List, Collection, Optional, Any

from data_to_paper.utils import dedent_triple_quote_str, word_count
from data_to_paper.utils.nice_list import NiceDict, NiceList
from data_to_paper.utils.print_to_file import print_and_log_red
from data_to_paper.servers.semantic_scholar import SEMANTIC_SCHOLAR_SERVER_CALLER, \
    SEMANTIC_SCHOLAR_EMBEDDING_SERVER_CALLER

from .request_python_value import PythonDictWithDefinedKeysReviewBackgroundProductsConverser
from .literature_search import LiteratureSearch, CitationCollectionProduct, QueryCitationCollectionProduct, \
    LiteratureSearchQueriesProduct
from ..interactive import PanelNames


@dataclass
class BaseLiteratureSearchReviewGPT(PythonDictWithDefinedKeysReviewBackgroundProductsConverser):
    number_of_papers_per_query: int = 100
    max_reviewing_rounds: int = 0
    literature_search: LiteratureSearch = field(default_factory=LiteratureSearch)
    domains_to_definitions_and_examples = {
        'dataset': {
            'definition': 'papers that use the same or similar datasets as in our study',
            'examples': ['The UK-NCD dataset', 'covid-19 vaccine efficacy dataset']
        },
        'questions': {
            'definition': 'papers that ask questions similar to our study',
            'examples': ['covid-19 vaccine efficacy over time', 'covid-19 vaccine waning']
        },
        'background': {
            'definition': 'papers that provide background on the overall subject of our study',
            'examples': ["SARS-CoV2 spread", "covid-19 global impact", "covid-19 vaccine"],
        },
        'methods': {
            'definition': 'papers that use the same or similar methods as in our study',
            'examples': ["covid-19 vaccine efficacy analysis", "kaplan-meier survival analysis"],
        },
        'results': {
            'definition': 'papers that report results similar to our study',
            'examples': ["covid-19 vaccine efficacy", "covid-19 vaccine efficacy over time", "covid-19 vaccine waning"],
        }
    }
    requested_keys: Collection[str] = ('dataset', 'questions',)

    excluded_citation_titles: List[str] = None
    # bibtex ids to remove from the results. Important for removing reproduced paper from citing itself.

    value_type: type = Dict[str, List[str]]
    goal_noun: str = 'literature search queries'
    goal_verb: str = 'write'
    mission_prompt: str = dedent_triple_quote_str("""
        Please write literature-search queries that we can use to search for papers related to our study.

        You would need to compose search queries to identify prior papers covering these {num_scopes} areas:
        {pretty_scopes_to_definitions}

        Return your answer as a `Dict[str, List[str]]`, where the keys are the {num_scopes} areas noted above, \t
        and the values are lists of query string. Each individual query should be a string with up to 5-10 words. 

        For example, for a study reporting waning of the efficacy of the covid-19 BNT162b2 vaccine based on analysis \t
        of the "United Kingdom National Core Data (UK-NCD)", the queries could be:
        ```python
        {pretty_scopes_to_examples}
        ```  
        """)

    @property
    def chosen_domains_to_definitions_and_examples(self) -> Dict[str, Dict[str, str]]:
        return {key: self.domains_to_definitions_and_examples[key] for key in self.requested_keys}

    @property
    def pretty_scopes_to_definitions(self) -> str:
        return '\n'.join([f'"{scope}": {definition_and_examples["definition"]}'
                          for scope, definition_and_examples
                          in self.chosen_domains_to_definitions_and_examples.items()])

    @property
    def pretty_scopes_to_examples(self) -> str:
        return ('{\n' +
                '\n'.join([f'    "{scope}": {definition_and_examples["examples"]}'
                           for scope, definition_and_examples
                           in self.chosen_domains_to_definitions_and_examples.items()]) +
                '\n}')

    @property
    def num_scopes(self) -> int:
        return len(self.requested_keys)

    def get_title(self) -> Optional[str]:
        """
        Returns the title of the paper we are writing.
        None to skip building embedding vector.
        """
        return None

    def get_abstract(self) -> Optional[str]:
        """
        Returns the abstract of the paper we are writing.
        None to skip building embedding vector.
        """
        return None

    def _check_response_value(self, response_value: dict) -> NiceDict:
        super()._check_response_value(response_value)
        # The queries are 'valid' even if they have too many words:
        self._update_valid_result(response_value)
        too_long_queries = []
        for queries in response_value.values():
            for query in queries:
                if word_count(query) > 10:
                    too_long_queries.append(query)
        if too_long_queries:
            self._raise_self_response_error(dedent_triple_quote_str("""
                Queries should be 5-10 word long.

                The following queries are too long:
                {}

                Please return your complete response again, with these queries shortened.
                """).format(NiceList(too_long_queries, wrap_with='"', prefix='', suffix='', separator='\n')))
        return NiceDict({k: NiceList(v, wrap_with='"', prefix='[\n' + ' ' * 8, suffix='\n' + ' ' * 4 + ']',
                                     separator=',\n' + ' ' * 8)
                         for k, v in response_value.items()})

    def get_literature_search(self) -> LiteratureSearch:
        scopes_to_list_of_queries = self.run_and_get_valid_result()
        literature_search = self.literature_search
        server_name = SEMANTIC_SCHOLAR_SERVER_CALLER.name
        html = f'<h2>Querying Citations</h2>'
        html += f'<p>Searching "{server_name}" ' \
                f'for papers related to our study in the following areas:</p>'
        self._app_set_status(PanelNames.FEEDBACK, 'Querying citations...')
        for scope, queries in scopes_to_list_of_queries.items():
            queries_to_citations = {}
            html += f'<h3>{scope.title()}-related queries:</h3>'
            for query in queries:
                citations = SEMANTIC_SCHOLAR_SERVER_CALLER.get_server_response(query,
                                                                               rows=self.number_of_papers_per_query)
                num_citations = len(citations)
                html += f'<p>Query: "{query}". Found {num_citations} citations.</p>'
                self._app_send_prompt(PanelNames.FEEDBACK, html, provided_as_html=True)
                self.comment(f'\nQuerying Semantic Scholar. '
                             f'Found {num_citations} / {self.number_of_papers_per_query} citations. '
                             f'Query: "{query}".')
                if self.excluded_citation_titles is not None:
                    excluded_citations = [citation for citation in citations
                                          if citation['title'] in self.excluded_citation_titles]
                    if excluded_citations:
                        print_and_log_red(
                            f'The following citations specified in the excluded citation list were excluded:\n')
                        for citation in excluded_citations:
                            print_and_log_red(f'{citation}\n\n')
                        citations = QueryCitationCollectionProduct(
                            query=query,
                            value=[citation for citation in citations if citation not in excluded_citations])

                queries_to_citations[query] = citations

            literature_search[scope] = queries_to_citations

        # Calculate embedding vector
        if self.get_title() is not None and self.get_abstract() is not None:
            literature_search.embedding_target = \
                SEMANTIC_SCHOLAR_EMBEDDING_SERVER_CALLER.get_server_response({
                    "paper_id": "",
                    "title": self.get_title(),
                    "abstract": self.get_abstract()})

        self._app_request_continue()
        return literature_search

    def _update_valid_result(self, valid_result: Any):
        super()._update_valid_result(LiteratureSearchQueriesProduct(value=valid_result))
