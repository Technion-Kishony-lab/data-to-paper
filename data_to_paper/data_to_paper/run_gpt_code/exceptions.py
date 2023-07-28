from abc import ABCMeta
from dataclasses import dataclass
from typing import List, Optional

from data_to_paper.exceptions import data_to_paperException


class RunCodeException(data_to_paperException, metaclass=ABCMeta):
    """
    Base class for all exceptions related to running gpt provided code.
    """
    pass


@dataclass
class FailedRunningCode(RunCodeException):
    exception: Exception
    tb: Optional[List]
    fake_file_name = "my_analysis.py"

    def __str__(self):
        return f"Running the code resulted in the following exception:\n{self.exception}\n"

    def get_traceback_message(self, lines_added_by_modifying_code: int = 0):
        """
        returns a fake traceback message, simulating as if the code ran in a real file.
        the line causing the exception is extracted from the ran `code`.
        """
        if isinstance(self.exception, SyntaxError):
            lineno = self.exception.lineno
            text = self.exception.text
            msg = self.exception.msg
        else:
            from data_to_paper.run_gpt_code.dynamic_code import module_filename
            index = next((i for i, t in enumerate(self.tb) if t[0].endswith(module_filename)), None)
            if index is None:
                return ''
            filename, lineno, funcname, text = self.tb[index]
            msg = self.exception

        return f'  File "{self.fake_file_name}", line {lineno - lines_added_by_modifying_code}, in <module>"\n' + \
               f'    {text}\n' + \
               f'{type(self.exception).__name__}: {msg}'


class CodeTimeoutException(RunCodeException, TimeoutError):
    def __str__(self):
        return "Code took too long to run."


class BaseRunContextException(RunCodeException, metaclass=ABCMeta):
    pass


@dataclass
class CodeUsesForbiddenFunctions(BaseRunContextException):
    func: str

    def __str__(self):
        return f"Code uses a forbidden function {self.func}."


@dataclass
class CodeImportForbiddenModule(BaseRunContextException):
    module: str

    def __str__(self):
        return f"Code import a forbidden module {self.module}."


@dataclass
class CodeWriteForbiddenFile(BaseRunContextException):
    file: str

    def __str__(self):
        return f"Code tries to create a forbidden file {self.file}."


@dataclass
class CodeReadForbiddenFile(BaseRunContextException):
    file: str

    def __str__(self):
        return f"Code tries to load a forbidden file {self.file}."
