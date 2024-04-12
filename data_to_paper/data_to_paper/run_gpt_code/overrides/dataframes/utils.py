from contextlib import contextmanager

import pandas as pd

from data_to_paper.env import NUM_DIGITS_FOR_FLOATS


def format_float(value: float, float_format: str = None) -> str:
    float_format = float_format or f'.{NUM_DIGITS_FOR_FLOATS}g'

    if value.is_integer():
        return str(int(value))
    else:
        return f'{value:{float_format}}'


@contextmanager
def temporarily_change_float_format(new_format):
    """
    Context manager that temporarily changes the float format to the given format.
    """
    original_float_format = pd.get_option('display.float_format')
    try:
        pd.set_option(f'display.float_format', new_format)
        yield
    finally:
        pd.set_option(f'display.float_format', original_float_format)
