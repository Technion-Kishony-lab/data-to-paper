from typing import Iterable, Optional


FILEDS_TO_NAMES = {
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
}


class Citation(dict):
    """
    A citation of a paper.
    """

    def __init__(self, *args, search_rank: int = None, query: str = None, **kwargs):
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
        return NotImplemented

    @property
    def bibtex_id(self) -> str:
        return NotImplemented

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
    def journal_and_year(self) -> Optional[str]:
        if self.journal is None or self.year is None:
            return None
        return f'{self.journal} ({self.year})'

    def pretty_repr(self,
                    fields: Iterable[str] = ('bibtex_id', 'title', 'journal_and_year', 'tldr', 'influence'),
                    is_html: bool = False,
                    ) -> str:
        """
        Get a pretty representation of the citation.
        Allows specifying which fields to include.
        """
        if is_html:
            return self.to_html(fields)
        s = ''
        for field in fields:
            name = FILEDS_TO_NAMES[field]
            value = getattr(self, field, field)
            if value is None:
                continue
            s += f'{name}: {repr(value)}\n'
        s += '\n'
        return s

    def to_html(self,
                fields: Iterable[str] = ('bibtex_id', 'title', 'journal_and_year', 'tldr', 'influence'),
                ) -> str:
        """
        Get an HTML representation of the citation.
        Allows specifying which fields to include.
        """
        s = ''
        for field in fields:
            name = FILEDS_TO_NAMES[field]
            value = getattr(self, field, field)
            if value is None:
                continue
            s += f'<b>{name}</b>: {repr(value)}<br>'
        return s

    def __str__(self):
        return self.pretty_repr()

    def __repr__(self):
        return self.__str__()
