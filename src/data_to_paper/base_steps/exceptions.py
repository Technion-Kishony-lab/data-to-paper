from dataclasses import dataclass

from data_to_paper.terminate.exceptions import TerminateException


@dataclass
class FailedCreatingProductException(TerminateException):
    reason: str

    def __str__(self):
        return self.reason
