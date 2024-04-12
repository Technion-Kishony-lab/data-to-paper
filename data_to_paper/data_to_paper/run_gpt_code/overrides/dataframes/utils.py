from contextlib import contextmanager

import pandas as pd
from pandas import DataFrame

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


def to_string_with_iterables(df, original_method=None, float_format=None, **kwargs):
    # Function to format individual numbers
    def format_elem(x):
        if isinstance(x, (int, float)):
            return float_format(x) if float_format else str(x)
        return x

    # Function to format iterables
    def format_iterable(iterable):
        if isinstance(iterable, (tuple, list)):
            return type(iterable)(format_elem(e) for e in iterable)
        return iterable

    # Apply formatting to each cell in the dataframe
    formatted_df = df.applymap(format_iterable)
    original_method = original_method or DataFrame.to_string
    return original_method(formatted_df, float_format=float_format, **kwargs)
