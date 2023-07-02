from dataclasses import dataclass

from data_to_paper.exceptions import data_to_paperException


@dataclass(frozen=True)
class FailedCreatingProductException(data_to_paperException):
    def __str__(self):
        return f"Failed to create product."
