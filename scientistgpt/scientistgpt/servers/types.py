from typing import Iterable, Optional


class Citation(dict):
    """
    A citation of a paper.
    """

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
    def journal_and_year(self) -> Optional[str]:
        if self.journal is None or self.year is None:
            return None
        return f'{self.journal} ({self.year})'

    def pretty_repr(self,
                    fields: Iterable[str] = ('bibtex_id', 'title', 'journal_and_year', 'tldr'),
                    names: Iterable[str] = ('ID', 'Title', 'Journal and Year', 'TLDR'),
                    ) -> str:
        """
        Get a pretty representation of the citation.
        Allows specifying which fields to include.
        """
        s = ''
        for field, name in zip(fields, names):
            value = getattr(self, field, None)
            if value is None:
                continue
            s += f'{name}: {value}\n'
        s += '\n'
        return s

    def __str__(self):
        return self.pretty_repr()

    def __repr__(self):
        return self.__str__()
