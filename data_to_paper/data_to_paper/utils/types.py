import collections
from enum import Enum

from typing import Generic, TypeVar, Iterable


class IndexOrderedEnum(Enum):

    def _get_index(self):
        """
        Get the index of this enum value in the list of enum values.
        """
        return self._member_names_.index(self.name)

    def get_next(self):
        """
        Get the next enum value in the list.
        If this is the last value, a ValueError is raised.
        """
        return list(self.__class__)[(self._get_index() + 1)]

    def __eq__(self, other):
        if isinstance(other, IndexOrderedEnum):
            return self._get_index() == other._get_index()
        return NotImplemented

    def __lt__(self, other):
        if isinstance(other, IndexOrderedEnum):
            return self._get_index() < other._get_index()
        return NotImplemented

    def __le__(self, other):
        if isinstance(other, IndexOrderedEnum):
            return self._get_index() <= other._get_index()
        return NotImplemented

    def __gt__(self, other):
        if isinstance(other, IndexOrderedEnum):
            return self._get_index() > other._get_index()
        return NotImplemented

    def __ge__(self, other):
        if isinstance(other, IndexOrderedEnum):
            return self._get_index() >= other._get_index()
        return NotImplemented


T = TypeVar('T')


class ListBasedSet(collections.abc.Set, Generic[T]):
    """
    Alternate set implementation favoring space over speed and stable ordering.
    also and not requiring the set elements to be hashable.
    """

    def __init__(self, iterable: Iterable = None):
        self.elements = lst = []
        if iterable is not None:
            for value in iterable:
                if value not in lst:
                    lst.append(value)

    def __iter__(self):
        return iter(self.elements)

    def __contains__(self, value):
        return value in self.elements

    def __len__(self):
        return len(self.elements)

    def __str__(self):
        # make it look like a set:
        return '{' + ', '.join(repr(e) for e in self) + '}'

    def add(self, value):
        if value not in self.elements:
            self.elements.append(value)
