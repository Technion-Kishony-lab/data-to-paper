from abc import ABC
from dataclasses import dataclass
from typing import List

from scientistgpt.exceptions import ScientistGPTException


# TODO:  we will not be using this exception anymore. Remove after cleaning up _choose_citations_for_sentence
@dataclass
class CitationException(ScientistGPTException):
    """
    Base class for all citation adding errors.
    """
    message: str = None

    def __str__(self):
        return self.message


# TODO:  we will not be using this exception anymore. Remove after cleaning up _choose_citations_for_sentence
class WrongFormatCitationException(CitationException):
    """
    Error raised when the user did not return the results in the correct format.
    """
    pass


@dataclass
class NotInSectionException(ScientistGPTException):
    """
    Error raised when the user did not return the results in the correct format.
    """
    sentences: List[str] = None

    def __str__(self):
        return f'The following sentences are not in the specified section: {self.sentences}'


# TODO:  we will not be using this exception anymore. Remove after cleaning up _choose_citations_for_sentence
class NotInCitationsCitationException(CitationException):
    """
    Error raised when the user did not return the citations that are inside the possible citations.
    """
    pass


@dataclass
class ServerErrorCitationException(ScientistGPTException):
    """
    Error raised server wasn't able to respond.
    """
    status_code: int
    text: str

    def __str__(self):
        return f"Request failed with status code {self.status_code}, error: {self.text}"
