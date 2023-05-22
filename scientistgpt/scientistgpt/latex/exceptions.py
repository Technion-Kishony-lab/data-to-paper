from dataclasses import dataclass
from typing import Optional

from scientistgpt.exceptions import ScientistGPTException


@dataclass
class FailedToExtractLatexContent(ScientistGPTException, ValueError):
    """
    Raised when the latex content could not be extracted from the response.
    """
    reason: str

    def __str__(self):
        return self.reason


@dataclass(frozen=True)
class LatexCompilationError(ScientistGPTException, ValueError):
    """
    Raised when the latex content could not be compiled.
    """
    latex_content: str
    pdflatex_output: str

    def _extract_error_message(self) -> str:
        """
        Extract the error message from the pdflatex output.
        """
        lines = self.pdflatex_output.splitlines()
        first_line_of_error_message = next((i for i, line in enumerate(lines) if line.startswith('! ')), None)
        return '\n'.join(lines[first_line_of_error_message:first_line_of_error_message + 3])

    def get_latex_exception_line_number(self) -> Optional[int]:
        """
        Get the line number of the latex exception.
        """
        error_message = self._extract_error_message()
        if '\nl.' not in error_message:
            return None
        return int(error_message.split('\nl.')[1].split(' ')[0]) - 1  # -1 because the latex line numbers start at 1

    def _get_erroneous_lines(self) -> Optional[str]:
        """
        Get the erroneous lines from the latex content.
        """
        error_line = self.get_latex_exception_line_number()
        if error_line is None:
            return None
        return '\n'.join(self.latex_content.splitlines()[error_line - 1:error_line + 2])

    def __str__(self):
        erroneous_lines = self._get_erroneous_lines()
        if erroneous_lines is None:
            return f'Failed to compile latex due to the following pdflatex error:\n\n' \
                   f'```\n' \
                   f'{self._extract_error_message()}' \
                   f'```\n'
        return f'Failed to compile latex due to problem in these lines:\n{self._get_erroneous_lines()}\n\n' \
               f'Got the following pdflatex error:\n' \
               f'```\n' \
               f'{self._extract_error_message()}' \
               f'```\n'
