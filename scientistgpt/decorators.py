import functools
import signal
import threading
import os

from scientistgpt.exceptions import CodeTimeoutException


def confirm_output(prompt='DO YOU APPROVE?'):
    """
    A decorator that presents the output of a function to the user, asks for approval,
    and raises an exception if the output is not approved.

    Args:
        prompt (str): The prompt message to be presented to the user.

    Returns:
        The decorated function.
    """

    def decorator_confirm_output(func):

        @functools.wraps(func)
        def wrapper_confirm_output(*args, **kwargs):
            output = func(*args, **kwargs)
            print("-------------")
            print(output)
            while True:
                response = input(prompt + '(y/n)').lower()
                if response == 'y':
                    return output
                elif response == 'n':
                    raise ValueError("Output not approved.")
                else:
                    print("Invalid response. Please enter 'y' or 'n'.")

        return wrapper_confirm_output

    return decorator_confirm_output


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
