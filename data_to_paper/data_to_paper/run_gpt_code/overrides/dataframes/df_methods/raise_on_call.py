from dataclasses import dataclass


@dataclass
class UnAllowedDataframeMethodCall(Exception):
    method_name: str

    def __str__(self):
        return f"Calling dataframe method '{self.method_name}' is not allowed."


def raise_on_call(*args, original_method=None, on_change=None, **kwargs):
    raise UnAllowedDataframeMethodCall(method_name=original_method.__name__)
