from enum import Enum


class IndexOrderedEnum(Enum):

    def _get_index(self):
        return self._member_names_.index(self.name)

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
