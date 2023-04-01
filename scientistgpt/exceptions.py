from abc import abstractmethod, ABCMeta
from dataclasses import dataclass
from typing import List


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
        if isinstance(self.exception, SyntaxError):
            lineno = self.exception.lineno
            text = self.exception.text
            msg = self.exception.msg
        else:
            from scientistgpt.dynamic_code import module_filename
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


class UserRejectException(ScientistGPTException):
    def __str__(self):
        return "Output was disapproved by user."


@dataclass
class FailedRunningStep(ScientistGPTException):
    step: int
    func_name: str

    def __str__(self):
        return f"Failed running {self.func_name} (step {self.step})"


class FailedDebuggingException(ScientistGPTException):
    def __str__(self):
        return f"Failed debugging chatgpt code."
