from copy import copy

import numpy as np

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Iterable

from data_to_paper.utils.iterators import interleave
from data_to_paper.utils.mutable import Mutable
from data_to_paper.utils.nice_list import NiceList
from data_to_paper.servers.types import Citation


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


CITATION_REPR_FIELDS_FOR_CHATGPT = \
    ('bibtex_id', 'title', 'journal_and_year', 'tldr', 'influence')
CITATION_REPR_FIELDS_FOR_PRINT = \
    ('query', 'search_rank', 'bibtex_id', 'title', 'journal_and_year', 'tldr', 'influence', 'embedding_similarity')


@dataclass
class LiteratureSearch:
    scopes_to_queries_to_citations: Dict[str, Dict[str, List[Citation]]] = field(default_factory=dict)
    embedding_target: Optional[np.ndarray] = None

    def get_queries(self, scope: Optional[str] = None) -> List[str]:
        """
        Return the queries in the given scope.
        if scope=None, return all queries.
        """
        if scope is None:
            queries = sum([self.get_queries(scope) for scope in self.scopes_to_queries_to_citations], [])
        else:
            queries = list(self.scopes_to_queries_to_citations[scope].keys())
        return NiceList(queries, wrap_with='"', separator='\n', prefix='\n', suffix='\n')

    def get_citations(self, scope: Optional[str] = None, query: Optional[str] = None,
                      total: int = None, distribution_factor: Optional[float] = None,
                      sort_by_similarity: bool = False, minimal_influence: int = 0) -> List[Citation]:
        """
        Return the citations in the given scope.
        If embedding_target is not None, sort the citations by embedding similarity.
        If total is not None, return only the first total citations.
        If total < 0, return only the last total citations.
        """
        if scope is None:
            assert query is None
            citations = unite_citation_lists((self.get_citations(
                    scope=scope,
                    total=int(total / len(self.scopes_to_queries_to_citations) * distribution_factor) + 1
                    if distribution_factor and total is not None else None,
                    minimal_influence=minimal_influence,
                    distribution_factor=distribution_factor,
                    sort_by_similarity=sort_by_similarity,
            ) for scope in self.scopes_to_queries_to_citations))
        elif query is None:
            citations = unite_citation_lists((self.get_citations(
                    scope=scope,
                    query=query,
                    total=int(total / len(self.scopes_to_queries_to_citations[scope]) * distribution_factor) + 1
                    if distribution_factor and total is not None else None,
                    minimal_influence=minimal_influence,
                    distribution_factor=distribution_factor,
                    sort_by_similarity=sort_by_similarity,
                ) for query in self.scopes_to_queries_to_citations[scope]))
        else:
            citations = self.scopes_to_queries_to_citations[scope][query]
        citations = list(citations)

        if minimal_influence > 0:
            citations = [citation for citation in citations if citation.influence >= minimal_influence]

        if sort_by_similarity and self.embedding_target is not None:
            citations = sorted(citations, key=lambda citation: citation.get_embedding_similarity(self.embedding_target),
                               reverse=True)
        else:
            citations = sorted(citations, key=lambda citation: citation.search_rank)

        if total is None:
            return citations
        if total < 0:
            return citations[total:]
        else:
            return citations[:total]

    def pretty_repr(self, with_scope_and_queries: bool = False,
                    total: int = None, distribution_factor: Optional[float] = None,
                    sort_by_similarity: bool = False,
                    minimal_influence: int = 0,
                    style: str = None,
                    ) -> str:
        s = ''
        for scope in self.scopes_to_queries_to_citations:
            if with_scope_and_queries:
                s += '\n\n'
                s += f'Scope: {repr(scope)}\n'
                s += f'Queries: {repr(self.get_queries(scope))}\n'
            s += self.pretty_repr_for_scope_and_query(scope=scope,
                                                      total=total // len(self.scopes_to_queries_to_citations) + 1,
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
        style: 'chatgpt', 'print', 'html'
        """
        style = style or 'chatgpt'
        citations = self.get_citations(scope=scope, query=query, total=total,
                                       distribution_factor=distribution_factor,
                                       sort_by_similarity=sort_by_similarity,
                                       minimal_influence=minimal_influence,
                                       )
        return '\n'.join(citation.pretty_repr(
            fields=CITATION_REPR_FIELDS_FOR_CHATGPT if style == 'chatgpt' else CITATION_REPR_FIELDS_FOR_PRINT,
            is_html=style == 'html',
            embedding_target=self.embedding_target,
        ) for citation in citations)

    def get_citation(self, bibtex_id: str) -> Optional[Citation]:
        for citation in self.get_citations():
            if citation.bibtex_id == bibtex_id:
                return citation
        return None
