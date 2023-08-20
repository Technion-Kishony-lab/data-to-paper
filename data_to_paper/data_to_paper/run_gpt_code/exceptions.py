import traceback
from abc import ABCMeta
from dataclasses import dataclass
from typing import List, Optional, Tuple

from data_to_paper.exceptions import data_to_paperException


@dataclass
class FailedRunningCode(data_to_paperException):
    exception: Exception
    tb: Optional[List]
    fake_file_name = "my_analysis.py"

    @classmethod
    def from_exception(cls, e: Exception):
        return cls(exception=e, tb=traceback.extract_tb(e.__traceback__))

    def __str__(self):
        return f"Running the code resulted in the following exception:\n{self.exception}\n"

    def _get_gpt_module_frames(self):
        """
        returns the frame(s) of the module that was created by gpt.
        """
        if self.tb is None:
            return None

        from data_to_paper.run_gpt_code.dynamic_code import module_filename

        return [t for t in self.tb if t[0].endswith(module_filename)]

    def _get_name_space(self):
        """
        returns the name space of the frame that caused the exception.
        """
        # TODO: implement
        return NotImplemented

    def get_lineno_line_message(self, lines_added_by_modifying_code: int = 0) -> Tuple[List[Tuple[int, str]], str]:
        """
        returns the line of code that caused the exception.
        """
        if isinstance(self.exception, SyntaxError):
            lineno = self.exception.lineno
            text = self.exception.text
            linenos_and_lines = [(lineno, text)]
            msg = self.exception.msg
        else:
            msg = str(self.exception)
            frames = self._get_gpt_module_frames()
            linenos_and_lines = [(f.lineno, f.line) for f in frames]
        linenos_and_lines = [(lineno - lines_added_by_modifying_code, text) for lineno, text in linenos_and_lines]
        return linenos_and_lines, msg

    def get_traceback_message(self, lines_added_by_modifying_code: int = 0):
        """
        returns a fake traceback message, simulating as if the code ran in a real file.
        the line causing the exception is extracted from the ran `code`.
        """
        linenos_and_lines, msg = self.get_lineno_line_message(lines_added_by_modifying_code)
        s = ''
        for lineno, line in linenos_and_lines:
            s += f'  File "{self.fake_file_name}", line {lineno}, in <module>"\n' + \
               f'    {line}\n'
        return s + f'{type(self.exception).__name__}: {msg}'


class BaseRunContextException(data_to_paperException, metaclass=ABCMeta):
    pass


@dataclass
class CodeTimeoutException(BaseRunContextException, TimeoutError):
    time: int

    def __str__(self):
        return f"Code timeout after {self.time} seconds."


@dataclass
class UnAllowedFilesCreated(BaseRunContextException, PermissionError):
    un_allowed_files: List[str]

    def __str__(self):
        return f'UnAllowedFilesCreated: {self.un_allowed_files}'


@dataclass
class CodeUsesForbiddenFunctions(BaseRunContextException):
    func: str

    def __str__(self):
        return f"Code uses a forbidden function `{self.func}`."


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
