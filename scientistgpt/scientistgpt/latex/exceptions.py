from dataclasses import dataclass

from scientistgpt.exceptions import ScientistGPTException


@dataclass
class FailedToExtractLatexContent(ScientistGPTException, ValueError):
    """
    Raised when the latex content could not be extracted from the response.
    """
    reason: str

    def __str__(self):
        return self.reason
