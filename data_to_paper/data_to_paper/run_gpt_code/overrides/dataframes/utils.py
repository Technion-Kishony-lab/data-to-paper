import numbers
from contextlib import contextmanager
from functools import partial
from typing import Callable, Any

import pandas as pd
from pandas import DataFrame

from data_to_paper.env import NUM_DIGITS_FOR_FLOATS
from data_to_paper.run_gpt_code.overrides.dataframes.df_methods.to_latex import to_latex_with_escape
from data_to_paper.run_gpt_code.overrides.dataframes.original_methods import get_original_df_method


def format_numeric_value(value: numbers.Number, float_format: str = None) -> str:
    float_format = float_format or f'.{NUM_DIGITS_FOR_FLOATS}g'

    if isinstance(value, int) or value.is_integer():
        return str(int(value))
    else:
        return f'{value:{float_format}}'


def format_numerics_and_iterables(value: Any, numeric_formater: Callable = None, object_formatter: Callable = None):
    numeric_formater = numeric_formater or format_numeric_value
    object_formatter = object_formatter or (lambda x: x)
    if isinstance(value, numbers.Number):
        return numeric_formater(value)
    if isinstance(value, (tuple, set, list)):
        return type(value)(format_numerics_and_iterables(v, numeric_formater) for v in value)
    elif isinstance(value, dict):
        return {k: format_numerics_and_iterables(v, numeric_formater) for k, v in value.items()}
    return object_formatter(value)


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


def _get_formatters_for_df(df: DataFrame, numeric_formater: Callable = None, object_formatter: Callable = None):
    formater = partial(format_numerics_and_iterables, numeric_formater=numeric_formater, object_formatter=object_formatter)
    formatters = {}
    for column in df.columns:
        formatters[column] = formater
    return formatters


def to_string_with_format_value(df: DataFrame, *args,
                                numeric_formater: Callable = None,
                                object_formatter: Callable = None, **kwargs):
    to_string = get_original_df_method('to_string')
    return to_string(df, *args, formatters=_get_formatters_for_df(df, numeric_formater, object_formatter), **kwargs)


def to_latex_with_value_format(df: DataFrame, *args,
                               numeric_formater: Callable = None,
                               object_formatter: Callable = None, **kwargs):
    to_latex = get_original_df_method('to_latex')
    return to_latex_with_escape(df, *args, original_method=to_latex,
                                formatters=_get_formatters_for_df(df, numeric_formater, object_formatter), **kwargs)


def to_html_with_value_format(df: DataFrame, *args,
                              numeric_formater: Callable = None,
                              object_formatter: Callable = None, **kwargs):
    to_html = get_original_df_method('to_html')
    return to_html(df, *args, formatters=_get_formatters_for_df(df, numeric_formater, object_formatter), **kwargs)
