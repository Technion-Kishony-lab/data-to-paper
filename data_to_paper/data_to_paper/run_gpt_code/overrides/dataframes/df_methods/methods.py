from contextlib import contextmanager
from dataclasses import dataclass

import pandas as pd
from pandas.core.frame import DataFrame

from data_to_paper.env import PDF_TEXT_WIDTH

from ..utils import format_float
from ..dataframe_operations import SaveDataframeOperation, CreationDataframeOperation, \
    ChangeSeriesDataframeOperation, AddSeriesDataframeOperation, RemoveSeriesDataframeOperation


@dataclass
class DataframeKeyError(KeyError):
    original_error: KeyError
    key: str
    dataframe: DataFrame

    def __str__(self):
        return str(self.original_error) + f"\n\nAvailable keys are: {list(self.dataframe.columns)}"


ORIGINAL_FLOAT_FORMAT = pd.get_option('display.float_format')
TO_CSV_FLOAT_FORMAT = ORIGINAL_FLOAT_FORMAT
STR_FLOAT_FORMAT = format_float


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


def __init__(self, *args, created_by: str = None, file_path: str = None,
             original_method=None, on_change=None, **kwargs):
    original_method(self, *args, **kwargs)
    self.created_by = created_by
    self.file_path = file_path
    on_change(self, CreationDataframeOperation(
        id=id(self), created_by=created_by, file_path=file_path, columns=list(self.columns.values)))


def __getitem__(self, key, original_method=None, on_change=None):
    try:
        return original_method(self, key)
    except KeyError as e:
        raise DataframeKeyError(original_error=e, key=key, dataframe=self)


def __setitem__(self, key, value, original_method=None, on_change=None):
    if hasattr(self, 'columns'):
        original_columns = self.columns
    else:
        original_columns = None
    result = original_method(self, key, value)
    if original_columns is not None:
        if isinstance(key, (list, tuple)):
            is_changing_existing_columns = any(k in original_columns for k in key)
        else:
            is_changing_existing_columns = key in original_columns
        operation_type = ChangeSeriesDataframeOperation if is_changing_existing_columns else AddSeriesDataframeOperation
        on_change(self, operation_type(id=id(self), series_name=key))
    return result


def __delitem__(self, key, original_method=None, on_change=None):
    result = original_method(self, key)
    on_change(self, RemoveSeriesDataframeOperation(id=id(self), series_name=key))
    return result


def __str__(self, original_method=None, on_change=None):
    # to avoid printing with [...] skipping columns
    return self.to_string()


def to_string(self, *args, original_method=None, on_change=None, **kwargs):
    """
    We print with short floats, avoid printing with [...] skipping columns, and checking which orientation to use.
    """
    with temporarily_change_float_format(STR_FLOAT_FORMAT):
        result1 = original_method(self, *args, **kwargs)
        result2 = original_method(self.T, *args, **kwargs)
    longest_line1 = max(len(line) for line in result1.split('\n'))
    longest_line2 = max(len(line) for line in result2.split('\n'))
    if longest_line1 > PDF_TEXT_WIDTH > longest_line2:
        result = result2
    else:
        result = result1
    return result


def to_csv(self, *args, original_method=None, on_change=None, **kwargs):
    with temporarily_change_float_format(TO_CSV_FLOAT_FORMAT):
        result = original_method(self, *args, **kwargs)

    file_path = args[0] if len(args) > 0 else kwargs.get('path_or_buf')
    columns = list(self.columns.values) if hasattr(self, 'columns') else None
    on_change(self, SaveDataframeOperation(id=id(self), file_path=file_path, columns=columns))
    return result
