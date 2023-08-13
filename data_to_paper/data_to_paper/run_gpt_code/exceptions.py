from abc import ABCMeta
from dataclasses import dataclass
from typing import List, Optional, Tuple

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

    def _get_gpt_module_frame(self):
        """
        returns the frame of the module that was created by gpt.
        """
        if self.tb is None:
            return None

        from data_to_paper.run_gpt_code.dynamic_code import module_filename

        last_index = next((i for i, t in list(enumerate(self.tb))[::-1] if t[0].endswith(module_filename)), None)
        if last_index is None:
            return None

        return self.tb[last_index]

    def _get_name_space(self):
        """
        returns the name space of the frame that caused the exception.
        """
        # TODO: implement
        return NotImplemented

    def get_lineno_line_message(self, lines_added_by_modifying_code: int = 0
                                ) -> Tuple[Optional[int], Optional[str], str]:
        """
        returns the line of code that caused the exception.
        """
        if isinstance(self.exception, SyntaxError):
            lineno = self.exception.lineno
            text = self.exception.text
            msg = self.exception.msg
        else:
            from data_to_paper.run_gpt_code.dynamic_code import module_filename
            msg = str(self.exception)
            frame = self._get_gpt_module_frame()
            if frame is None:
                return None, None, msg
            filename, lineno, funcname, text = frame
        return lineno - lines_added_by_modifying_code, text, msg

    def get_traceback_message(self, lines_added_by_modifying_code: int = 0):
        """
        returns a fake traceback message, simulating as if the code ran in a real file.
        the line causing the exception is extracted from the ran `code`.
        """
        lineno, line, msg = self.get_lineno_line_message(lines_added_by_modifying_code)
        if lineno is None:
            s = ''
        else:
            s = f'  File "{self.fake_file_name}", line {lineno}, in <module>"\n' + \
               f'    {line}\n'
        return s + f'{type(self.exception).__name__}: {msg}'


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
