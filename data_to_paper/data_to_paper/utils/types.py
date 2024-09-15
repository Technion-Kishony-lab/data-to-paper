import collections
from enum import Enum

from typing import Generic, TypeVar, Iterable


class IndexOrderedEnum(Enum):

    def get_index(self):
        """
        Get the index of this enum value in the list of enum values.
        """
        return self._member_names_.index(self.name)

    def get_next(self):
        """
        Get the next enum value in the list.
        If this is the last value, a ValueError is raised.
        """
        try:
            return list(self.__class__)[(self.get_index() + 1)]
        except IndexError:
            raise ValueError(f"No next value after {self}")

    @classmethod
    def get_first(cls):
        return list(cls)[0]

    @classmethod
    def get_last(cls):
        return list(cls)[-1]

    def __eq__(self, other):
        if isinstance(other, IndexOrderedEnum):
            return self.get_index() == other.get_index()
        return NotImplemented

    def __lt__(self, other):
        if isinstance(other, IndexOrderedEnum):
            return self.get_index() < other.get_index()
        return NotImplemented

    def __le__(self, other):
        if isinstance(other, IndexOrderedEnum):
            return self.get_index() <= other.get_index()
        return NotImplemented

    def __gt__(self, other):
        if isinstance(other, IndexOrderedEnum):
            return self.get_index() > other.get_index()
        return NotImplemented

    def __ge__(self, other):
        if isinstance(other, IndexOrderedEnum):
            return self.get_index() >= other.get_index()
        return NotImplemented

    def __hash__(self):
        return hash(self.get_index())


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

    def __repr__(self):
        return f'{self.__class__.__name__}({self.elements})'

    def add(self, value):
        if value not in self.elements:
            self.elements.append(value)

    def remove(self, value):
        self.elements.remove(value)

    def update(self, other):
        for value in other:
            self.add(value)

    def union(self, other):
        return self.__class__(self.elements + list(other))


K = TypeVar('K')
V = TypeVar('V')


class MemoryDict(Generic[K, V]):
    def __init__(self):
        self._data = {}

    def __getitem__(self, key):
        return self._data[key][-1]['value']  # Retrieve the most recent value

    def __setitem__(self, key, value):
        if key not in self._data:
            self._data[key] = [{'name': 'default', 'value': value}]
        else:
            self._data[key].append({'name': 'default', 'value': value})

    def add_named_value(self, key, name, value):
        if key not in self._data:
            self._data[key] = [{'name': name, 'value': value}]
        else:
            self._data[key].append({'name': name, 'value': value})

    def get_named_value(self, key, name):
        if key in self._data:
            for item in reversed(self._data[key]):
                if item['name'] == name:
                    return item['value']
        return None

    def get_all_values(self, key):
        return [item['value'] for item in self._data.get(key, [])]

    def get_all_named_values(self, key):
        return [(item['name'], item['value']) for item in self._data.get(key, [])]

    def as_dict(self):
        return {key: self[key] for key in self._data}

    def items(self):
        return self.as_dict().items()

    def __delitem__(self, key):
        if key in self._data:
            del self._data[key]

    def __contains__(self, key):
        return key in self._data

    def __len__(self):
        return len(self._data)
