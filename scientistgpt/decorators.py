import functools
import time
import signal


def retry(func=None, *, default_retries=3, exception=Exception, delay=0.0):
    """
    A decorator that runs the decorated function multiple times until it passes without raising a specified exception.

    Args:
        default_retries (int): number of times to retry running the function
        func (callable): The function to be decorated.
        exception (Type[Exception])): The exception(s) that the decorated function may raise.
        delay (float): The delay in seconds between retries.

    Returns:
        The decorated function.
    """

    def decorator_retry(func):

        @functools.wraps(func)
        def wrapper_retry(*args, **kwargs):
            retries = kwargs.pop('retries', default_retries)
            for count in range(retries):
                if count > 0:
                    print(f'Retrying ({count + 1}/{retries})')
                try:
                    return func(*args, **kwargs)
                except exception as e:
                    print(f'Run failed with:\n {e}\n')
                    time.sleep(delay)
            raise e

        return wrapper_retry

    if func is None:
        return decorator_retry
    else:
        return decorator_retry(func)


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
    def decorator(func):
        def wrapper(*args, **kwargs):
            def signal_handler(signum, frame):
                raise TimeoutError(f"Function {func.__name__} timed out after {seconds} seconds")

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
