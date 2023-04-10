import signal
import threading
import os

from .exceptions import CodeTimeoutException


def timeout(seconds):
    """
    Decorator to terminate a function if runtime is too long.
    """

    # return different decorator depending on the operating system
    if os.name == 'nt':
        return timeout_windows(seconds)
    else:
        return timeout_unix(seconds)


def timeout_unix(seconds):
    def decorator(func):
        def wrapper(*args, **kwargs):
            def signal_handler(signum, frame):
                raise CodeTimeoutException(f"Function {func.__name__} timed out after {seconds} seconds")

            # Set the signal handler and alarm for the specified number of seconds
            signal.signal(signal.SIGALRM, signal_handler)
            signal.alarm(seconds)

            try:
                # Call the function with the provided arguments
                result = func(*args, **kwargs)
            finally:
                # Cancel the alarm when the function completes
                signal.alarm(0)

            return result

        return wrapper

    return decorator


def timeout_windows(seconds):
    def decorator(func):
        def wrapper(*args, **kwargs):
            result_container = {'result': None}
            exception_container = {'exception': None}
            stop_event = threading.Event()

            def target():
                try:
                    result_container['result'] = func(*args, **kwargs)
                except Exception as e:
                    exception_container['exception'] = e
                finally:
                    stop_event.set()

            worker_thread = threading.Thread(target=target)
            worker_thread.start()
            worker_thread.join(timeout=seconds)

            if not stop_event.is_set():
                raise CodeTimeoutException(f"Function {func.__name__} timed out after {seconds} seconds")

            if exception_container['exception'] is not None:
                raise exception_container['exception']

            return result_container['result']

        return wrapper

    return decorator
