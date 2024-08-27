from dataclasses import dataclass
from typing import Any


@dataclass
class SerializableValue:
    """
    Base class for a serializable value.
    """

    value: Any

    def _serialize_value(self):
        return self.value

    @classmethod
    def _start_with(cls) -> str:
        return f'{cls.__name__}: '

    def serialize(self):
        return f'{self._start_with()}{self._serialize_value()}'

    @classmethod
    def from_serialized_value(cls, serialized_value: str):
        return cls(serialized_value)

    @classmethod
    def deserialize(cls, serialized: str):
        if serialized.startswith(cls._start_with()):
            return cls.from_serialized_value(serialized[len(cls._start_with()):])
        raise ValueError(f'Unknown serialized object: {serialized}')


def get_all_subclasses(cls):
    all_subclasses = []

    for subclass in cls.__subclasses__():
        all_subclasses.append(subclass)
        all_subclasses.extend(get_all_subclasses(subclass))

    return all_subclasses


def deserialize_serializable_value(serialized: str) -> SerializableValue:
    """
    Deserializes a serialized object.
    """
    # iterate over all subclasses AND their subclasses
    for cls in get_all_subclasses(SerializableValue):
        try:
            return cls.deserialize(serialized)
        except ValueError:
            pass
    raise ValueError(f'Unknown serialized object: {serialized}')
