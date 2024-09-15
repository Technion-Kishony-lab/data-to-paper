from typing import Iterable, Optional, Union, Set

import numpy as np

FIELDS_TO_NAMES = {
    'bibtex_id': 'ID',
    'title': 'Title',
    'journal': 'Journal',
    'journal_and_year': 'Journal and year',
    'tldr': 'TLDR',
    'abstract': 'Abstract',
    'year': 'Year',
    'influence': 'Citation influence',
    'query': 'Query',
    'search_rank': 'Search rank',
    'embedding_similarity': 'Embedding similarity',
}


class Citation(dict):
    """
    A citation of a paper.
    """

    def __init__(self, *args, search_rank: int = None, query: Union[str, Set[str]] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.search_rank = search_rank
        self.query = query

    def __key(self):
        return self.bibtex_id

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    @property
    def bibtex(self) -> str:
        raise NotImplementedError

    @property
    def bibtex_id(self) -> str:
        raise NotImplementedError

    @property
    def title(self) -> Optional[str]:
        return None

    @property
    def tldr(self) -> Optional[str]:
        return None

    @property
    def abstract(self) -> Optional[str]:
        return None

    @property
    def journal(self) -> Optional[str]:
        return None

    @property
    def year(self) -> Optional[str]:
        return None

    @property
    def influence(self) -> int:
        return 0

    @property
    def embedding(self) -> Optional[np.ndarray]:
        return None

    @property
    def journal_and_year(self) -> Optional[str]:
        if self.journal is None or self.year is None:
            return None
        return f'{self.journal} ({self.year})'

    def get_embedding_similarity(self, embedding_target: Optional[np.ndarray]) -> float:
        if self.embedding is None or embedding_target is None:
            return 0
        return np.dot(self.embedding, embedding_target) / \
            (np.linalg.norm(self.embedding) * np.linalg.norm(embedding_target))

    def pretty_repr(self,
                    fields: Iterable[str] = ('bibtex_id', 'title', 'journal_and_year', 'tldr', 'influence'),
                    is_html: bool = False,
                    embedding_target: float = None,
                    ) -> str:
        """
        Get a pretty representation of the citation.
        Allows specifying which fields to include.
        """
        s = ''
        for field in fields:
            name = FIELDS_TO_NAMES[field]
            if field == 'embedding_similarity':
                value = self.get_embedding_similarity(embedding_target)
                value = None if value is None else round(value, 2)
            else:
                value = getattr(self, field, field)
            if field == 'query' and isinstance(value, set):
                value = sorted(value)
            if value is None:
                continue
            if is_html:
                # name in bold
                s += f'<b>{name}</b>: {value}<br>'
            else:
                s += f'{name}: {repr(value)}\n'
        if is_html:
            s += '<br>'
        else:
            s += '\n'
        return s

    def __str__(self):
        return self.pretty_repr()

    def __repr__(self):
        return self.__str__()
