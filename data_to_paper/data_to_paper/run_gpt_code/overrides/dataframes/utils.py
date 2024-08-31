import numbers
from contextlib import contextmanager
from functools import partial
from typing import Callable, Any

import numpy as np
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
    object_formatter = object_formatter or (lambda x: str(x))
    if isinstance(value, numbers.Number):
        return numeric_formater(value)
    if isinstance(value, tuple):
        return '(' + ', '.join(format_numerics_and_iterables(v, numeric_formater) for v in value) + ')'
    elif isinstance(value, list):
        return '[' + ', '.join(format_numerics_and_iterables(v, numeric_formater) for v in value) + ']'
    elif isinstance(value, dict):
        return '{' + ', '.join(f'{k}: {format_numerics_and_iterables(v, numeric_formater)}'
                               for k, v in value.items()) + '}'
    elif isinstance(value, np.ndarray):
        return '[' + ', '.join(format_numerics_and_iterables(v, numeric_formater) for v in value) + ']'
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
    formater = partial(format_numerics_and_iterables, numeric_formater=numeric_formater,
                       object_formatter=object_formatter)
    return [formater] * df.shape[1]


def df_to_string_with_format_value(df: DataFrame, *args,
                                   numeric_formater: Callable = None,
                                   object_formatter: Callable = None, **kwargs):
    to_string = get_original_df_method('to_string')
    return to_string(df, *args, formatters=_get_formatters_for_df(df, numeric_formater, object_formatter), **kwargs)


def df_to_latex_with_value_format(df: DataFrame, *args,
                                  numeric_formater: Callable = None,
                                  object_formatter: Callable = None, **kwargs):
    to_latex = get_original_df_method('to_latex')
    return to_latex_with_escape(df, *args, original_method=to_latex,
                                formatters=_get_formatters_for_df(df, numeric_formater, object_formatter), **kwargs)


def df_to_html_with_value_format(df: DataFrame, *args,
                                 numeric_formater: Callable = None,
                                 object_formatter: Callable = None, **kwargs):
    to_html = get_original_df_method('to_html')
    return to_html(df, *args, formatters=_get_formatters_for_df(df, numeric_formater, object_formatter), **kwargs)


def df_to_llm_readable_csv(df, index_label='index',
                           numeric_formater: Callable = None,
                           object_formatter: Callable = None):
    """
    Convert a DataFrame to a CSV string that is easy to parse by the LLM.
    Takes care of:
    - Quoting string values
    - Quoting column names
    - Quoting index values
    - Formatting lists, tuples, and dictionaries
    - Specifying the index label
    - Multi-level column headers
    - Multi-level indices
    """
    output = []

    # Handle multi-level column headers
    if isinstance(df.columns, pd.MultiIndex):
        for level in range(df.columns.nlevels):
            if index_label and df.index.nlevels > 0:  # Add blank spaces for the index label in header rows
                level_header = [index_label] * df.index.nlevels
            else:
                level_header = []
            level_header += ['"{}"'.format(col) for col in df.columns.get_level_values(level)]
            output.append(','.join(level_header))
    else:
        # Single level columns
        header = ['"{}"'.format(col) for col in df.columns]
        if index_label and df.index.nlevels > 0:
            header = [index_label] * df.index.nlevels + header
        output.append(','.join(header))

    # Handle multi-level indices and quote string indices
    for index, row in df.iterrows():
        index_part = list(index) if isinstance(index, tuple) else [index]
        # Quote strings in index parts
        formatted_index = [f'"{item}"' if isinstance(item, str) else str(item) for item in index_part]
        formatted_row = formatted_index

        for item in row:
            formatted_row.append(str(format_numerics_and_iterables(item, numeric_formater, object_formatter)))
        output.append(','.join(formatted_row))

    return '\n'.join(output)
