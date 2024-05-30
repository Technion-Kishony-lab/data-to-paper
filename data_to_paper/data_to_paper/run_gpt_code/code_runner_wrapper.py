import os
import pickle
import platform
import threading
import tempfile
import uuid

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Tuple, Any

from data_to_paper.env import MAX_EXEC_TIME
from data_to_paper.utils.mutable import Mutable
from data_to_paper.run_gpt_code.code_runner import CodeRunner, is_serializable

from .base_run_contexts import MultiRunContext
from .cache_runs import CacheRunToFile
from .exceptions import FailedRunningCode, CodeTimeoutException
from ..utils.types import ListBasedSet

# process.queue fails on Mac OS X with large objects. Use file-based transfer instead.
RUN_CACHE_FILEPATH = Mutable(None)


@dataclass
class CodeRunnerWrapper(CacheRunToFile):
    code: str = None  # code to run
    timeout_sec: int = MAX_EXEC_TIME.val
    code_runner: CodeRunner = field(default_factory=CodeRunner)
    run_in_separate_process: bool = True
    cache_filepath: Path = field(default_factory=lambda: RUN_CACHE_FILEPATH.val)  # None if not caching

    @property
    def run_folder(self):
        return self.code_runner.run_folder

    def run_code(self) -> Tuple[Any, ListBasedSet[str], MultiRunContext, Optional[FailedRunningCode]]:
        return self.code_runner.run(code=self.code)

    def _get_run_directory(self):
        return self.run_folder

    def _get_instance_key(self) -> tuple:
        return (self.code, )

    def run(self, *args, **kwargs) -> Tuple[Any, ListBasedSet[str], MultiRunContext, Optional[FailedRunningCode]]:
        return super().run(*args, **kwargs)

    def _run(self):
        if self.run_in_separate_process:
            return self.run_code_in_separate_process()
        return self.code_runner.run(code=self.code)

    def run_code_in_separate_process(self) \
            -> Tuple[Any, ListBasedSet[str], MultiRunContext, Optional[FailedRunningCode]]:
        """
        Run the provided code in a separate process and report exceptions or specific warnings.
        Calls `run_in_provided_process` which is a wrapper for `run`.
        """
        code = self.get_raw_code()
        modified_code = self.get_modified_code_for_run(code)
        queue_or_filepath = f"subprocess_output_{uuid.uuid4()}_{os.getpid()}.pkl"
        queue_or_filepath = os.path.join(tempfile.gettempdir(), queue_or_filepath)
        try:
            process = threading.Thread(
                target=self._run_code_and_put_result_in_queue,
                args=(queue_or_filepath, ),
            )
        except (AttributeError, TypeError):
            for k, v in self.__dict__.items():
                if not is_serializable(v):
                    print(f'Attribute {k} is not serializable.')
            raise
        process.start()
        process.join(self.timeout_sec)
        if process.is_alive():
            with os.popen(f'{"sudo -n " if platform.system() == "Darwin" else ""}py-spy dump --pid {process.pid}') as f:
                py_spy_stack = f.read()
            process.join()
            result = (
                None,
                [],
                dict(),
                FailedRunningCode.from_exception_with_py_spy(CodeTimeoutException(self.timeout_sec),
                                                             (py_spy_stack, code)))
        else:
            with open(queue_or_filepath, 'rb') as f:
                result = pickle.load(f)
            os.remove(queue_or_filepath)
            if isinstance(result, Exception):
                raise result
        return result

    def _run_code_and_put_result_in_queue(self, queue_or_filepath):
        """
        Run the provided code and put the result in the queue.
        """
        try:
            result = self.code_runner.run(code=self.code)
        except Exception as e:
            result = e
        with open(queue_or_filepath, 'wb') as f:
            pickle.dump(result, f)
