from abc import abstractmethod, ABCMeta
from dataclasses import is_dataclass, fields


class data_to_paperException(Exception, metaclass=ABCMeta):
    """
    Base class for all exceptions in this package.
    """
    @abstractmethod
    def __str__(self):
        pass

    def __reduce__(self):
        if is_dataclass(self):
            # Collect the field values in the order they're defined in the dataclass
            field_values = [getattr(self, f.name) for f in fields(self)]
            return (self.__class__, tuple(field_values))
        else:
            # Fallback for non-dataclass exceptions
            return super().__reduce__()
