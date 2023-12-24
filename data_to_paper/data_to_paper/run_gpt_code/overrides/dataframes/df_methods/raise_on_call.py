from dataclasses import dataclass

from data_to_paper.exceptions import data_to_paperException


@dataclass
class UnAllowedDataframeMethodCall(data_to_paperException):
    method_name: str

    def __str__(self):
        return f"Calling dataframe method '{self.method_name}' is not allowed."


def raise_on_call(*args, original_method=None, on_change=None, **kwargs):
    raise UnAllowedDataframeMethodCall(method_name=original_method.__name__)
