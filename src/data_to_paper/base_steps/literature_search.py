from copy import copy

import numpy as np

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Iterable, NamedTuple

from data_to_paper.base_products.product import ValueProduct
from data_to_paper.code_and_output_files.file_view_params import ViewPurpose
from data_to_paper.utils.iterators import interleave
from data_to_paper.utils.mutable import Flag
from data_to_paper.utils.nice_list import NiceList
from data_to_paper.servers.custom_types import Citation


def unite_citation_lists(citations_lists: Iterable[Iterable[Citation]], total: int = None) -> List[Citation]:
    """
    Unite the two lists maintaining a single bibtex_id for each citation.
    Citation that appears in both list will have the query as a set of both quereis.
    """
    bibtex_ids_to_citations = {}
    for citation in interleave(*citations_lists):
        bibtex_id = citation.bibtex_id
        query = citation.query
        if isinstance(query, str):
            query = {query}
        if bibtex_id not in bibtex_ids_to_citations:
            citation = copy(citation)
            citation.query = query
            bibtex_ids_to_citations[bibtex_id] = citation
        else:
            bibtex_ids_to_citations[bibtex_id].query.update(query)
            bibtex_ids_to_citations[bibtex_id].search_rank = min(bibtex_ids_to_citations[bibtex_id].search_rank,
                                                                 citation.search_rank)
        if total is not None:
            if len(bibtex_ids_to_citations) == total:
                break
    return list(bibtex_ids_to_citations.values())


CITATION_REPR_FIELDS_FOR_LLM = \
    ('bibtex_id', 'title', 'journal_and_year', 'tldr', 'influence')
CITATION_REPR_FIELDS_FOR_PRINT = \
    ('query', 'search_rank', 'bibtex_id', 'title', 'journal_and_year', 'tldr', 'influence', 'embedding_similarity')
GET_LITERATURE_SEARCH_FOR_PRINT = Flag(False)


@dataclass
class LiteratureSearchQueriesProduct(ValueProduct):
    name: str = "Literature Search Queries"
    value: Dict[str, List[str]] = None

    def _get_content_as_formatted_text(self, level: int, view_purpose: ViewPurpose, **kwargs) -> str:
        s = ''
        level_str = '#' * (level + 1)
        for scope, queries in self.value.items():
            s += f'{level_str} {scope.title()}\n'
            for query in queries:
                s += f'- "{query}"\n'
        return s


@dataclass
class CitationCollectionProduct(ValueProduct):
    name: str = "Citation List"
    value: List[Citation] = None

    def __iter__(self) -> Iterable[Citation]:
        return super().__iter__()

    def _get_citations_as_str(self, is_html: bool, style: str = None,
                              embedding_target: Optional[np.ndarray] = None) -> str:
        return '\n'.join(citation.pretty_repr(
            fields=CITATION_REPR_FIELDS_FOR_LLM if style == 'llm' else CITATION_REPR_FIELDS_FOR_PRINT,
            is_html=is_html,
            embedding_target=embedding_target,
        ) for citation in self.value)

    def _get_content_as_formatted_text(self, level: int, view_purpose: ViewPurpose, style: str = None,
                                       embedding_target: Optional[np.ndarray] = None, **kwargs: str) -> str:
        return self._get_citations_as_str(is_html=False, style=style, embedding_target=embedding_target)

    def _get_content_as_html(self, level: int, style: str = None,
                             embedding_target: Optional[np.ndarray] = None):
        return self._get_citations_as_str(is_html=True, style=style)


@dataclass
class QueryCitationCollectionProduct(CitationCollectionProduct):
    name: str = "Query Citation List"
    query: str = None

    def get_header(self, view_purpose: ViewPurpose = ViewPurpose.PRODUCT, **kwargs) -> str:
        return f'{self.name} for "{self.query}"'


@dataclass
class SortedCitationCollectionProduct(CitationCollectionProduct):
    name: str = "Sorted Citation List"
    scope: Optional[str] = None
    query: Optional[str] = None
    total: int = None
    distribution_factor: Optional[float] = None
    sort_by_similarity: bool = False
    minimal_influence: int = 0

    def get_header(self, view_purpose: ViewPurpose = ViewPurpose.PRODUCT, style: str = 'llm', **kwargs) -> str:
        s = super().get_header()
        s += f', Scope: "{self.scope}"' if self.scope is not None else ''
        s += f', Query: "{self.query}"' if self.query is not None else ''
        if style != 'llm':
            s += f', Total: {self.total}' if self.total is not None else ''
            s += f', Distribution Factor: {self.distribution_factor}' if self.distribution_factor is not None else ''
            s += f', Sort by Similarity: {self.sort_by_similarity}' if self.sort_by_similarity else ''
            s += f', Minimal Influence: {self.minimal_influence}' if self.minimal_influence > 0 else ''
        return s


class LiteratureSearchParams(NamedTuple):
    total: int
    minimal_influence: int
    distribution_factor: Optional[float]
    sort_by_similarity: bool

    def to_dict(self) -> dict:
        return self._asdict()


@dataclass
class LiteratureSearch(ValueProduct):
    # value is scopes_to_queries_to_citations
    value: Dict[str, Dict[str, CitationCollectionProduct]] = field(default_factory=dict)
    embedding_target: Optional[np.ndarray] = None
    scopes_to_search_params: Dict[str, LiteratureSearchParams] = field(default_factory=dict)

    def get_queries(self, scope: Optional[str] = None) -> List[str]:
        """
        Return the queries in the given scope.
        if scope=None, return all queries.
        """
        if scope is None:
            queries = sum([self.get_queries(scope) for scope in self], [])
        else:
            queries = list(self[scope].keys())
        return NiceList(queries, wrap_with='"', separator='\n', prefix='\n', suffix='\n')

    def get_citations(self, scope: Optional[str] = None, query: Optional[str] = None,
                      total: int = None, distribution_factor: Optional[float] = None,
                      sort_by_similarity: bool = False, minimal_influence: int = 0) -> CitationCollectionProduct:
        """
        Return the citations in the given scope.
        If embedding_target is not None, sort the citations by embedding similarity.
        If total is not None, return only the first total citations.
        If total < 0, return only the last total citations.
        """
        if scope is None:
            assert query is None
            citations = unite_citation_lists((iter(self.get_citations(
                    scope=scope,
                    total=int(total / len(self) * distribution_factor) + 1
                    if distribution_factor and total is not None else None,
                    minimal_influence=minimal_influence,
                    distribution_factor=distribution_factor,
                    sort_by_similarity=sort_by_similarity,
            )) for scope in self))
        elif query is None:
            citations = unite_citation_lists((iter(self.get_citations(
                    scope=scope,
                    query=query,
                    total=int(total / len(self[scope]) * distribution_factor) + 1
                    if distribution_factor and total is not None else None,
                    minimal_influence=minimal_influence,
                    distribution_factor=distribution_factor,
                    sort_by_similarity=sort_by_similarity,
                )) for query in self[scope]))
        else:
            citations = self[scope][query]
        citations = list(citations)

        if minimal_influence > 0:
            citations = [citation for citation in citations if citation.influence >= minimal_influence]

        if sort_by_similarity and self.embedding_target is not None:
            citations = sorted(citations, key=lambda citation: citation.get_embedding_similarity(self.embedding_target),
                               reverse=True)
        else:
            citations = sorted(citations, key=lambda citation: citation.search_rank)

        if total is None:
            pass
        elif total < 0:
            citations = citations[total:]
        else:
            citations = citations[:total]
        return SortedCitationCollectionProduct(value=citations, scope=scope, query=query,
                                               total=total, distribution_factor=distribution_factor,
                                               sort_by_similarity=sort_by_similarity,
                                               minimal_influence=minimal_influence)

    def pretty_repr(self, with_scope_and_queries: bool = False,
                    total: int = None, distribution_factor: Optional[float] = None,
                    sort_by_similarity: bool = False,
                    minimal_influence: int = 0,
                    style: str = None,
                    ) -> str:
        s = ''
        for scope in self:
            if with_scope_and_queries:
                s += '\n\n'
                s += f'Scope: {repr(scope)}\n'
                s += f'Queries: {repr(self.get_queries(scope))}\n'
            s += self.pretty_repr_for_scope_and_query(scope=scope,
                                                      total=total // len(self) + 1,
                                                      distribution_factor=distribution_factor,
                                                      sort_by_similarity=sort_by_similarity,
                                                      minimal_influence=minimal_influence,
                                                      style=style)
        return s

    def pretty_repr_for_scope_and_query(self, scope: str, query: Optional[str] = None,
                                        total: int = None, distribution_factor: Optional[float] = None,
                                        sort_by_similarity: bool = False,
                                        minimal_influence: int = 0,
                                        style: str = None) -> str:
        """
        style: 'llm', 'print', 'html'
        """
        style = style or 'llm'
        citations = self.get_citations(scope=scope, query=query, total=total,
                                       distribution_factor=distribution_factor,
                                       sort_by_similarity=sort_by_similarity,
                                       minimal_influence=minimal_influence,
                                       )
        if GET_LITERATURE_SEARCH_FOR_PRINT:
            style = 'print'
        return '\n'.join(citation.pretty_repr(
            fields=CITATION_REPR_FIELDS_FOR_LLM if style == 'llm' else CITATION_REPR_FIELDS_FOR_PRINT,
            is_html=style == 'html',
            embedding_target=self.embedding_target,
        ) for citation in citations)

    def get_header(self, view_purpose: ViewPurpose = ViewPurpose.PRODUCT, scope: Optional[str] = None, **kwargs) -> str:
        return f'{scope}-related literature search' if scope is not None else self.name

    def _get_content_as_formatted_text(self, level: int, view_purpose: ViewPurpose,
                                       scope: Optional[str] = None, style: str = 'llm', **kwargs) -> str:
        if scope is None:
            s = ''
            for scope in self:
                s += self._get_content_as_formatted_text(level, view_purpose, scope=scope, style=style)
        else:
            s = self.pretty_repr_for_scope_and_query(scope=scope, style=style,
                                                     **self.scopes_to_search_params[scope].to_dict())
        return s

    def _get_content_as_html(self, level: int, scope: Optional[str] = None, style: str = 'html', **kwargs) -> str:
        if scope is None:
            s = 'We searched for papers in the following scopes:\n'
            for scope in self:
                s += f'<h{level + 1}>{scope.title()}-related papers</h{level + 1}>\n'
                s += self._get_content_as_html(level, scope=scope, style=style)
        else:
            s = self.pretty_repr_for_scope_and_query(scope=scope, style=style,
                                                     **self.scopes_to_search_params[scope].to_dict())
        return s
