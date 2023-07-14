from abc import abstractmethod, ABCMeta
from dataclasses import dataclass


class data_to_paperException(Exception, metaclass=ABCMeta):
    """
    Base class for all exceptions in this package.
    """
    @abstractmethod
    def __str__(self):
        pass


class UserRejectException(data_to_paperException):
    def __str__(self):
        return "Output was disapproved by user."


@dataclass
class FailedRunningStep(data_to_paperException):
    step: int
    func_name: str

    def __str__(self):
        return f"Failed running {self.func_name} (step {self.step})"
