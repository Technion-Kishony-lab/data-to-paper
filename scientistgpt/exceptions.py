import re
from abc import abstractmethod, ABCMeta
from dataclasses import dataclass
from typing import Callable, List


class ScientistGPTException(Exception, metaclass=ABCMeta):
    @abstractmethod
    def __str__(self):
        pass


class RunCodeException(ScientistGPTException, metaclass=ABCMeta):
    pass


@dataclass
class FailedExtractingCode(RunCodeException):
    number_of_codes: int

    def __str__(self):
        if self.number_of_codes == 0:
            return "No code was found."
        return "More than one code snippet were found."


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
        filenames = [t[0] for t in self.tb]
        index = filenames.index('<string>')
        filename, lineno, funcname, text = self.tb[index]
        return f'  File "{self.fake_file_name}", line {lineno}, in <module>"\n' + \
               f'    {self.code.splitlines()[lineno - 1]}\n' + \
               f'{type(self.exception).__name__}: {self.exception}'


class FailedLoadingOutput(RunCodeException, FileNotFoundError):
    def __str__(self):
        return "Output file not found."


class UserRejectException(ScientistGPTException):
    def __str__(self):
        return "Output was disapproved by user."


@dataclass
class FailedRunningStep(ScientistGPTException):
    step: int
    func_name: str

    def __str__(self):
        return f"Failed running {self.func_name} (step {self.step})"


class DebuggingFailedException(ScientistGPTException):
    def __str__(self):
        return f"Failed debugging chatgpt code."
