from dataclasses import dataclass
from typing import Optional

from data_to_paper.exceptions import data_to_paperException
from data_to_paper.text import wrap_as_block


@dataclass
class FailedToExtractLatexContent(data_to_paperException, ValueError):
    """
    Raised when the latex content could not be extracted from the response.
    """
    reason: str

    def __str__(self):
        return self.reason


@dataclass
class BaseLatexProblemInCompilation(data_to_paperException, ValueError):
    pass


@dataclass
class LatexProblemInCompilation(BaseLatexProblemInCompilation):
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

    @property
    def error_message(self) -> str:
        """
        Get the error message from the pdflatex output.
        """
        return wrap_as_block(self._extract_error_message(), 'error')

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
            message_header = f'There was a latex compilation problem.\n\n'
        else:
            message_header = f'There was a latex compilation problem in these lines:\n{erroneous_lines}\n\n'
        return f'{message_header}Got the following pdflatex error:\n{self.error_message}'


@dataclass
class LatexCompilationError(LatexProblemInCompilation):
    """
    Raised when the latex content could not be compiled.
    """
    problem_starting_term: str = '! '


@dataclass
class LatexNumCommandFormulaEvalError(BaseLatexProblemInCompilation):
    """
    Raised when there is an error evaluating the latex \num command.
    """
    expression: str
    exception: Exception

    def __str__(self):
        return f'Failed to evaluate the latex \\num command for the expression:\n{self.expression}\n' \
               f'Got the following exception:\n{self.exception}'


@dataclass
class LatexNumCommandNoExplanation(BaseLatexProblemInCompilation):
    """
    Raised when latex \num command missing an explanation.
    """
    expression: str

    def __str__(self):
        return (f'The latex \\num command must have two arguments: a formula and an explanation. '
                f'Expected format: \\num{{<formula>, "explanation"}}, but got:\n{self.expression}')


@dataclass
class LatexNestedNumCommandError(BaseLatexProblemInCompilation):
    """
    Raised when there is an error evaluating the latex \num command.
    """
    expression: str

    def __str__(self):
        return f'Nested \\num commands are not supported. In:\n{self.expression}'


@dataclass
class PlainNumberLatexNumCommandError(BaseLatexProblemInCompilation):
    """
    Raised when the latex \num command contains a plain number.
    """
    expression: str

    def __str__(self):
        return (f'The latex \\num command should only be used with a formula. '
                f'It should not be used for a plain number. In:\n{self.expression}')


@dataclass
class UnwantedCommandsUsedInLatex(data_to_paperException, ValueError):
    """
    Raised when the latex content contains unwanted commands.
    """
    unwanted_commands: list

    def __str__(self):
        return f'Unwanted commands used in latex:\n{self.unwanted_commands}\n'


@dataclass
class NonLatexCitations(data_to_paperException, ValueError):
    """
    Raised when there are citations that are not written using latex \\cite{} command.
    """
    non_latex_citations: list

    def __str__(self):
        return f'The following citations are not written using latex \\cite{{}} command:\n' \
               f'{self.non_latex_citations}\n\n' \
               f'Please use latex \\cite{{}} command to write citations.\n'
