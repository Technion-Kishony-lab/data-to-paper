import signal
import threading
import os
from contextlib import contextmanager


def timeout_context(seconds, exception=TimeoutError):
    """
    Context manager to terminate a function if runtime is too long.
    """

    # return different context manager depending on the operating system
    if os.name == 'nt':
        return timeout_windows_context(seconds, exception)
    else:
        return timeout_unix_context(seconds, exception)


@contextmanager
def timeout_unix_context(seconds, exception=TimeoutError):
    def signal_handler(signum, frame):
        raise exception(seconds)

    # Set the signal handler and alarm for the specified number of seconds
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)

    try:
        yield
    finally:
        # Cancel the alarm when the function completes
        signal.alarm(0)


@contextmanager
def timeout_windows_context(seconds, exception=TimeoutError):
    stop_event = threading.Event()

    def target():
        try:
            yield
        finally:
            stop_event.set()

    worker_thread = threading.Thread(target=target)
    worker_thread.start()
    worker_thread.join(timeout=seconds)

    if not stop_event.is_set():
        raise exception(seconds)
