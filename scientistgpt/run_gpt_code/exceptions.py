from abc import ABCMeta
from dataclasses import dataclass
from typing import List

from scientistgpt.exceptions import ScientistGPTException


class RunCodeException(ScientistGPTException, metaclass=ABCMeta):
    """
    Base class for all exceptions related to running gpt provided code.
    """
    pass


@dataclass
class FailedExtractingCode(RunCodeException):
    number_of_code_edges: int

    def __str__(self):
        if self.number_of_code_edges == 0:
            return "No code block was found."
        elif self.number_of_code_edges % 2 == 1:
            return "Code block is not closed."
        else:
            return "Multiple code blocks identified."


@dataclass
class FailedRunningCode(RunCodeException):
    exception: Exception
    tb: List
    code: str
    fake_file_name = "my_analysis.py"

    def __str__(self):
        return f"Running the code resulted in the following exception:\n{self.exception}\n"

    def get_traceback_message(self):
        """
        returns a fake traceback message, simulating as if the code ran in a real file.
        the line causing the exception is extracted from the ran `code`.
        """
        if isinstance(self.exception, SyntaxError):
            lineno = self.exception.lineno
            text = self.exception.text
            msg = self.exception.msg
        else:
            from scientistgpt.run_gpt_code.dynamic_code import module_filename
            index = next((i for i, t in enumerate(self.tb) if t[0].endswith(module_filename)), None)
            if index is None:
                return ''
            filename, lineno, funcname, text = self.tb[index]
            msg = self.exception

        return f'  File "{self.fake_file_name}", line {lineno}, in <module>"\n' + \
               f'    {text}\n' + \
               f'{type(self.exception).__name__}: {msg}'


class FailedLoadingOutput(RunCodeException, FileNotFoundError):
    def __str__(self):
        return "Output file not found."


class CodeTimeoutException(RunCodeException, TimeoutError):
    def __str__(self):
        return "Code took too long to run."
