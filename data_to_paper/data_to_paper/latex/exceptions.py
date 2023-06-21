from dataclasses import dataclass
from typing import Optional

from data_to_paper.exceptions import data_to_paperException


@dataclass
class FailedToExtractLatexContent(data_to_paperException, ValueError):
    """
    Raised when the latex content could not be extracted from the response.
    """
    reason: str

    def __str__(self):
        return self.reason


@dataclass
class LatexProblemInCompilation(data_to_paperException, ValueError):
    """
    Raised when the latex content could not be compiled.
    """
    latex_content: str
    pdflatex_output: str
    problem_starting_term: str

    def _extract_error_message(self) -> str:
        """
        Extract the error message from the pdflatex output.
        """
        lines = self.pdflatex_output.splitlines()
        first_line_of_error_message = next((i for i, line in enumerate(lines) if
                                            line.startswith(self.problem_starting_term)), None)
        return '\n'.join(lines[first_line_of_error_message:first_line_of_error_message + 4])

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
            return f'Problem to successfully compile latex due to the following problem or error:\n\n' \
                   f'```\n' \
                   f'{self._extract_error_message()}' \
                   f'```\n'
        return f'Problem to successfully compile latex due to these lines:\n{self._get_erroneous_lines()}\n\n' \
               f'Got the following problem or error:\n' \
               f'```\n' \
               f'{self._extract_error_message()}' \
               f'```\n'


@dataclass
class LatexCompilationError(LatexProblemInCompilation):
    """
    Raised when the latex content could not be compiled.
    """
    problem_starting_term: str = '! '

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


@dataclass
class UnwantedCommandsUsedInLatex(data_to_paperException, ValueError):
    """
    Raised when the latex content contains unwanted commands.
    """
    unwanted_commands: list

    def __str__(self):
        return f'Unwanted commands used in latex:\n{self.unwanted_commands}\n\n'


@dataclass
class NonLatexCitations(data_to_paperException, ValueError):
    """
    Raised when there are citations that are not written using latex \\cite{} command.
    """
    non_latex_citations: list

    def __str__(self):
        return f'The following citations are not written using latex \\cite{{}} command:\n' \
               f'{self.non_latex_citations}\n\n' \
               f'Please use latex \\cite{{}} command to write citations.\n\n'


@dataclass
class TooWideTableOrText(LatexProblemInCompilation):
    """
    Raised when the latex content contains a table or text that is too wide (Overfull hbox).
    """
    problem_starting_term: str = r'Overfull \hbox '

    def __str__(self):
        erroneous_lines = self._get_erroneous_lines()
        if erroneous_lines is None:
            return f'There was a problem with the latex compilation, the table or section you wrote was to wide ' \
                   f'to fit within the text width:\n\n' \
                   f'```\n' \
                   f'{self._extract_error_message()}' \
                   f'```\n' \
                   f'Try to shorten the text in the table or section you wrote or drop unnecessary columns.\n\n'
        return f'There was a problem with the latex compilation in these lines:\n{self._get_erroneous_lines()}\n\n' \
               f'The table or section you wrote was to wide to fit within the text width:\n' \
               f'```\n' \
               f'{self._extract_error_message()}' \
               f'```\n' \
               f'Try to shorten the text in the table or section you wrote or drop unnecessary columns.\n\n'
