from abc import ABCMeta
from dataclasses import dataclass
from typing import Optional, Union

from data_to_paper.conversation.stage import Stage
from data_to_paper.exceptions import data_to_paperException


class TerminateException(data_to_paperException, metaclass=ABCMeta):
    """
    Base class for all exceptions that terminate data-to-paper run.
    """
    pass


@dataclass
class MissingInstallationError(TerminateException):
    """
    An exception to indicate a missing installation.
    """
    package_name: str
    instructions: Optional[str] = None

    def __str__(self):
        s = f"{self.package_name} is not installed. Please install it."
        if self.instructions:
            s += f"\n\n{self.instructions.strip()}"
        return s


@dataclass
class ResetStepException(Exception):
    """
    An exception to reset the step.
    """
    stage: Optional[Union[Stage, bool]]  # reset to this stage, None to exit the app
