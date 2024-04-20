import contextlib
from dataclasses import dataclass
from typing import Any


@dataclass
class Mutable:
    val: Any

    def set(self, val: Any):
        self.val = val

    @contextlib.contextmanager
    def temporary_set(self, val):
        current = self.val
        self.set(val)
        try:
            yield
        finally:
            self.set(current)

    def __eq__(self, other):
        return self.val == other

    def __ne__(self, other):
        return self.val != other

    def __lt__(self, other):
        return self.val < other

    def __le__(self, other):
        return self.val <= other

    def __gt__(self, other):
        return self.val > other

    def __ge__(self, other):
        return self.val >= other

    def __bool__(self):
        return bool(self.val)


@dataclass
class Flag(Mutable):
    val: bool = False

    def __bool__(self):
        return self.val
