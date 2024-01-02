import multiprocessing
import os
import pickle
import platform
import tempfile
import uuid
from abc import abstractmethod, ABC
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Iterable, Tuple, List, Dict, Any, Type

from data_to_paper.env import MAX_EXEC_TIME
from data_to_paper.run_gpt_code.dynamic_code import RunCode, is_serializable
from data_to_paper.run_gpt_code.code_utils import extract_code_from_text
from data_to_paper.utils import line_count

from .exceptions import FailedRunningCode, CodeTimeoutException
from .code_and_output import CodeAndOutput
from .run_issues import RunIssue
from .output_file_requirements import OutputFileRequirements

# process.queue fails on Mac OS X with large objects. Use file-based transfer instead.
FILE_BASED_TRANSFER = True


@dataclass
class BaseCodeRunner(ABC):
    response: str = None  # response from ChatGPT (with code)
    script_file_path: Optional[Path] = None  # where to save the script after running. If None, don't save.
    run_folder: Optional[Path] = None
    output_file_requirements: OutputFileRequirements = OutputFileRequirements()
    allowed_read_files: Iterable[str] = ()
    additional_contexts: Optional[Dict[str, Any]] = None  # additional contexts to use when running code
    runtime_available_objects: dict = field(default_factory=dict)
    run_code_cls: Type[RunCode] = RunCode
    _lines_added_in_front_of_code: int = None
    timeout_sec: int = MAX_EXEC_TIME.val

    @property
    def lines_added_in_front_of_code(self) -> int:
        return self._lines_added_in_front_of_code

    @abstractmethod
    def get_raw_code(self) -> str:
        """
        Extract the raw code from the response.
        """
        return NotImplementedError

    def _modify_code(self, code: str) -> Tuple[str, int]:
        """
        Modify the raw code before running it.
        For example, add imports, change imports, etc.
        Return the modified code and the number of lines added in front of the code.
        """
        return code, 0

    def get_modified_code_for_run(self, code: str) -> str:
        """
        Get the actual code for running.
        """
        modified_code, self._lines_added_in_front_of_code = self._modify_code(code)
        return modified_code

    def get_run_code(self) -> RunCode:
        """
        Get the code for running.
        """
        return self.run_code_cls(
            allowed_open_read_files=self.allowed_read_files,
            allowed_open_write_files=None if self.output_file_requirements is None else
            self.output_file_requirements.get_all_allowed_created_filenames(),
            output_file_requirements=self.output_file_requirements,
            run_folder=self.run_folder,
            runtime_available_objects=self.runtime_available_objects,
            additional_contexts=self.additional_contexts,
        )

    def _get_code_and_output(self, code: str, result: str, created_files: Iterable[str],
                             contexts: Dict[str, Any] = None) -> CodeAndOutput:
        """
        Return the CodeAndOutput object for the given result and created files.
        """
        return CodeAndOutput(
            code=code,
            result=result,
            created_files=self.output_file_requirements.convert_to_output_file_requirements_with_content(
                created_files=created_files, run_folder=self.run_folder),
            dataframe_operations=contexts['TrackDataFrames'].dataframe_operations
            if 'TrackDataFrames' in contexts else None,
        )

    def run_code(self, code: Optional[str] = None, modified_code: Optional[str] = None) \
            -> Tuple[CodeAndOutput, List[RunIssue], Dict[str, Any], Optional[FailedRunningCode]]:
        """
        Run code from GPT response, and return the output and the code.
        """
        if code is None:
            code = self.get_raw_code()
        if modified_code is None:
            modified_code = self.get_modified_code_for_run(code)
        result, created_files, issues, contexts, exception = \
            self.get_run_code().run(code=modified_code, save_as=self.script_file_path)

        return self._get_code_and_output(code, result, created_files, contexts), issues, contexts, exception

    def run_code_in_separate_process(self) \
            -> Tuple[Optional[CodeAndOutput], List[RunIssue], Dict[str, Any], Optional[FailedRunningCode]]:
        """
        Run the provided code in a separate process and report exceptions or specific warnings.
        Calls `run_in_provided_process` which is a wrapper for `run`.
        """
        code = self.get_raw_code()
        modified_code = self.get_modified_code_for_run(code)
        if FILE_BASED_TRANSFER:
            queue_or_filepath = f"subprocess_output_{uuid.uuid4()}_{os.getpid()}.pkl"
            queue_or_filepath = os.path.join(tempfile.gettempdir(), queue_or_filepath)
        else:
            queue_or_filepath = multiprocessing.Queue()

        process = multiprocessing.Process(target=self._run_code_and_put_result_in_queue,
                                          args=(queue_or_filepath, code, modified_code))
        try:
            process.start()
        except (AttributeError, TypeError):
            for k, v in self.__dict__.items():
                if not is_serializable(v):
                    print(f'Attribute {k} is not serializable.')
            raise
        process.join(self.timeout_sec)
        if process.is_alive():
            with os.popen(f'{"sudo -n " if platform.system() == "Darwin" else ""}py-spy dump --pid {process.pid}') as f:
                py_spy_stack = f.read()
            process.terminate()
            process.join()
            result = (
                None,
                [],
                dict(),
                FailedRunningCode.from_exception_with_py_spy(CodeTimeoutException(self.timeout_sec),
                                                             (py_spy_stack, modified_code)))
        else:
            if FILE_BASED_TRANSFER:
                with open(queue_or_filepath, 'rb') as f:
                    result = pickle.load(f)
                os.remove(queue_or_filepath)
            else:
                result = queue_or_filepath.get()
            if isinstance(result, Exception):
                raise result  # unexpected exception; not from the run code
        return result

    def _run_code_and_put_result_in_queue(self, queue_or_filepath, code: str, modified_code: str):
        """
        Run the provided code and put the result in the queue.
        """
        try:
            result = self.run_code(code, modified_code)
        except Exception as e:
            result = e
        if FILE_BASED_TRANSFER:
            with open(queue_or_filepath, 'wb') as f:
                pickle.dump(result, f)
        else:
            queue_or_filepath.put(result)


@dataclass
class CodeRunner(BaseCodeRunner):
    """
    CodeRunner facilitates extracting and running Python code from chatGPT response::
    1. Extract code from GPT response.
    2. Run code, raise a relevant exception with text to send to chatGPT.
    3. Read the output file created by the run if successful.
    """

    add_in_front_of_code: str = ''

    def get_raw_code(self) -> str:
        return extract_code_from_text(self.response)

    def _modify_code(self, code: str) -> Tuple[str, int]:
        """
        Modify the extracted code before running it.
        """
        modified_code = self.add_in_front_of_code + code
        return modified_code, line_count(self.add_in_front_of_code)
