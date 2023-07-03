import numpy as np

from dataclasses import dataclass, field
from functools import reduce
from typing import Optional, Dict, List
from operator import or_

from data_to_paper.utils.mutable import Mutable
from data_to_paper.utils.nice_list import NiceList
from data_to_paper.utils.types import ListBasedSet
from data_to_paper.servers.types import Citation


def sort_citations_by_embedding_similarity(citations: List[Citation], embedding: np.ndarray) -> List[Citation]:
    """
    Sort the citations by embedding similarity.
    """
    if not citations:
        return []
    embeddings = np.array([citation['embedding'] for citation in citations])
    similarities = np.dot(embeddings, embedding)
    indices = np.argsort(similarities)[::-1]
    return [citations[i] for i in indices]


CITATION_REPR_FIELDS_FOR_CHATGPT = ('bibtex_id', 'title', 'journal_and_year', 'tldr', 'influence')
CITATION_REPR_FIELDS_FOR_PRINT = ('query', 'search_rank', 'bibtex_id', 'title', 'journal_and_year', 'influence')

CITATION_REPR_FIELDS = Mutable(CITATION_REPR_FIELDS_FOR_CHATGPT)


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
                      total: int = None, distribute_evenly: bool = True,
                      sort_by_similarity: bool = False, minimal_influence: int = 0) -> List[Citation]:
        """
        Return the citations in the given scope.
        If embedding_target is not None, sort the citations by embedding similarity.
        If total is not None, return only the first total citations.
        """
        empty = ListBasedSet()
        if scope is None:
            assert query is None
            citations = reduce(
                or_, [self.get_citations(
                    scope=scope,
                    total=total // len(self.scopes_to_queries_to_citations) + 1
                    if distribute_evenly and total is not None else None,
                    minimal_influence=minimal_influence,
                    distribute_evenly=distribute_evenly,
                ) for scope in self.scopes_to_queries_to_citations], empty)
        elif query is None:
            citations = reduce(
                or_, [self.get_citations(
                    scope=scope,
                    query=query,
                    total=total // len(self.scopes_to_queries_to_citations[scope]) + 1
                    if distribute_evenly and total is not None else None,
                    minimal_influence=minimal_influence,
                    distribute_evenly=distribute_evenly,
                ) for query in self.scopes_to_queries_to_citations[scope]], empty)
        else:
            citations = self.scopes_to_queries_to_citations[scope][query]
        citations = list(citations)

        if minimal_influence > 0:
            citations = [citation for citation in citations if citation.influence >= minimal_influence]

        if sort_by_similarity and self.embedding_target is not None:
            citations = sort_citations_by_embedding_similarity(citations, self.embedding_target)
        else:
            citations = sorted(citations, key=lambda citation: citation.search_rank)

        if total is None:
            return citations
        if total < 0:
            return citations[total:]
        else:
            return citations[:total]

    def pretty_repr(self, with_scope_and_queries: bool = False,
                    total: int = None, distribute_evenly: bool = True,
                    sort_by_similarity: bool = False,
                    minimal_influence: int = 0,
                    is_html: bool = False,
                    ) -> str:
        s = ''
        for scope in self.scopes_to_queries_to_citations:
            if with_scope_and_queries:
                s += '\n\n'
                s += f'Scope: {repr(scope)}\n'
                s += f'Queries: {repr(self.get_queries(scope))}\n'
            s += self.pretty_repr_for_scope_and_query(scope=scope,
                                                      total=total // len(self.scopes_to_queries_to_citations) + 1,
                                                      distribute_evenly=distribute_evenly,
                                                      sort_by_similarity=sort_by_similarity,
                                                      minimal_influence=minimal_influence,
                                                      is_html=is_html)
        return s

    def pretty_repr_for_scope_and_query(self, scope: str, query: Optional[str] = None,
                                        total: int = None, distribute_evenly: bool = True,
                                        sort_by_similarity: bool = False,
                                        minimal_influence: int = 0,
                                        is_html: bool = False) -> str:
        citations = self.get_citations(scope=scope, query=query, total=total,
                                       distribute_evenly=distribute_evenly,
                                       sort_by_similarity=sort_by_similarity,
                                       minimal_influence=minimal_influence,
                                       )
        return '\n'.join(citation.pretty_repr(fields=CITATION_REPR_FIELDS.val, is_html=is_html)
                         for citation in citations)

    def get_citation(self, bibtex_id: str) -> Optional[Citation]:
        for citation in self.get_citations():
            if citation.bibtex_id == bibtex_id:
                return citation
        return None
