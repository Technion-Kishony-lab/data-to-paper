import re
import traceback
from abc import ABCMeta
from dataclasses import dataclass
from typing import List, Optional, Tuple, Union

from data_to_paper.exceptions import data_to_paperException

from .user_script_name import module_filename, get_gpt_module_frames


@dataclass
class AnyException(data_to_paperException):
    msg: str
    type_name: str

    def __str__(self):
        return self.msg


def convert_exception_to_any_exception_if_needed(e: Exception) -> Exception:
    if isinstance(e, (TimeoutError, SyntaxError, ImportError, RuntimeWarning, FileNotFoundError,
                      data_to_paperException)):
        return e
    from .overrides.pvalue import is_p_value, OnStrPValue, OnStr
    msg = None
    if isinstance(e, KeyError):
        key = e.args[0]
        if is_p_value(key):
            msg = 'Using PValue as a key in mapping is mot allowed.\nDo not attempt to map or transform PValue(s).'
    if msg is None:
        with OnStrPValue(OnStr.WITH_ZERO):
            msg = str(e)
    return AnyException(msg, type_name=type(e).__name__)


@dataclass
class FailedRunningCode(data_to_paperException):
    exception: Optional[Union[Exception, AnyException]] = None
    tb: Optional[traceback.StackSummary] = None
    py_spy_stack_and_code: Optional[Tuple[str, str]] = ('', '')
    fake_file_name = "my_analysis.py"

    @classmethod
    def from_exception(cls, e: Exception):
        return cls(exception=convert_exception_to_any_exception_if_needed(e), tb=traceback.extract_tb(e.__traceback__))

    @classmethod
    def from_current_tb(cls, **kwargs):
        exception = kwargs.pop('exception', None)
        return cls(exception=exception, tb=traceback.extract_stack(), **kwargs)

    @classmethod
    def from_exception_with_py_spy(cls, e: Exception, py_spy_stack_and_code: Tuple[str, str]):
        return cls(exception=convert_exception_to_any_exception_if_needed(e), tb=traceback.extract_tb(e.__traceback__),
                   py_spy_stack_and_code=py_spy_stack_and_code)

    def __str__(self):
        return f"Running the code resulted in the following exception:\n{self.exception}\n"

    @property
    def linenos_and_lines(self):
        return self.get_lineno_line_message()[0]

    def _get_gpt_module_frames(self):
        """
        returns the frame(s) of the module that was created by gpt.
        """
        if self.tb is None:
            return None
        return get_gpt_module_frames(self.tb)

    def _extract_linono_line_from_py_spy_stack(self):
        """
        returns the line of code that caused the exception.
        """
        search_results = re.search(fr'{module_filename}:(\d+)', self.py_spy_stack_and_code[0])
        if search_results is None:
            return []
        lineno = search_results.group(1)
        line = self.py_spy_stack_and_code[1].splitlines()[int(lineno) - 1]
        return [(lineno, line)]

    def get_lineno_line_message(self, lines_added_by_modifying_code: int = 0) -> Tuple[List[Tuple[int, str]], str]:
        """
        returns the line of code that caused the exception.
        """
        if isinstance(self.exception, SyntaxError):
            lineno = self.exception.lineno
            text = self.exception.text
            linenos_and_lines = [(lineno, text)]
            msg = self.exception.msg
        elif isinstance(self.exception, TimeoutError) and self.py_spy_stack_and_code[0]:
            msg = str(self.exception)
            linenos_and_lines = self._extract_linono_line_from_py_spy_stack()
            return linenos_and_lines, msg
        else:
            msg = str(self.exception)
            frames = self._get_gpt_module_frames()
            if frames is None:
                linenos_and_lines = []
            else:
                linenos_and_lines = [(f.lineno, f.line) for f in frames]
        linenos_and_lines = [(lineno - lines_added_by_modifying_code, text) for lineno, text in linenos_and_lines]
        return linenos_and_lines, msg

    def get_type_name(self):
        if isinstance(self.exception, AnyException):
            return self.exception.type_name
        return type(self.exception).__name__

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
        return s + f'{self.get_type_name()}: {msg}'


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
