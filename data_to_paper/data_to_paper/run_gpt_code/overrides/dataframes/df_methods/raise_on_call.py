from dataclasses import dataclass


@dataclass
class UnAllowedDataframeMethodCall(Exception):
    method_name: str

    def __str__(self):
        return f"Calling dataframe method '{self.method_name}' is not allowed."


def raise_on_call(*args, method_name: str, **kwargs):
    raise UnAllowedDataframeMethodCall(method_name=method_name)
