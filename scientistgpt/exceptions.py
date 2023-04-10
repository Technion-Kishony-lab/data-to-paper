from abc import abstractmethod, ABCMeta
from dataclasses import dataclass


class ScientistGPTException(Exception, metaclass=ABCMeta):
    """
    Base class for all exceptions in this package.
    """
    @abstractmethod
    def __str__(self):
        pass


class UserRejectException(ScientistGPTException):
    def __str__(self):
        return "Output was disapproved by user."


@dataclass
class FailedRunningStep(ScientistGPTException):
    step: int
    func_name: str

    def __str__(self):
        return f"Failed running {self.func_name} (step {self.step})"
