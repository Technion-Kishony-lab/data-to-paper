from dataclasses import dataclass

from scientistgpt.exceptions import ScientistGPTException


@dataclass(frozen=True)
class FailedCreatingProductException(ScientistGPTException):
    def __str__(self):
        return f"Failed to create product."
