from abc import ABC
from dataclasses import dataclass
from typing import List

from scientistgpt.exceptions import ScientistGPTException


@dataclass
class CitationException(ScientistGPTException):
    """
    Base class for all citation adding errors.
    """
    message: str = None

    def __str__(self):
        return self.message


class WrongFormatCitationException(CitationException):
    """
    Error raised when the user did not return the results in the correct format.
    """
    pass


@dataclass
class NotInSectionCitationException(CitationException):
    """
    Error raised when the user did not return the results in the correct format.
    """
    sentences: List[str] = None


class NotInCitationsCitationException(CitationException):
    """
    Error raised when the user did not return the citations that are inside the possible citations.
    """
    pass


class ServerErrorCitationException(CitationException):
    """
    Error raised server wasn't able to respond.
    """
    pass