import signal
import threading
import os
from dataclasses import dataclass
from typing import Type

from data_to_paper.run_gpt_code.base_run_contexts import RegisteredRunContext


def timeout_context(seconds, exception=TimeoutError):
    """
    Context manager to terminate a function if runtime is too long.
    """

    # return different context manager depending on the operating system
    if os.name == 'nt':
        return TimeoutWindowsContext(seconds=seconds, exception=exception)
    else:
        return TimeoutUnixContext(seconds=seconds, exception=exception)


@dataclass
class BaseTimeoutContext(RegisteredRunContext):
    seconds: int = 10
    exception: Type[Exception] = TimeoutError


@dataclass
class TimeoutUnixContext(BaseTimeoutContext):

    def __enter__(self):
        signal.signal(signal.SIGALRM, self.signal_handler)
        signal.alarm(self.seconds)
        return super().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        signal.alarm(0)
        return super().__exit__(exc_type, exc_val, exc_tb)

    def signal_handler(self, signum, frame):
        raise self.exception(self.seconds)


@dataclass
class TimeoutWindowsContext(BaseTimeoutContext):

    def __enter__(self):
        self.stop_event = threading.Event()
        self.worker_thread = threading.Thread(target=self.target)
        self.worker_thread.start()
        self.worker_thread.join(timeout=self.seconds)
        return super().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.stop_event.is_set():
            raise self.exception(self.seconds)
        return super().__exit__(exc_type, exc_val, exc_tb)

    def target(self):
        try:
            yield
        finally:
            self.stop_event.set()