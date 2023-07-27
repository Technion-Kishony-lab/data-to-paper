from dataclasses import dataclass

import pandas as pd
from pandas.core.frame import DataFrame

from data_to_paper.env import PDF_TEXT_WIDTH

from ..override_dataframe import ON_CHANGE
from ..utils import format_float
from ..dataframe_operations import SaveDataframeOperation, CreationDataframeOperation, DataframeOperation, \
    ChangeSeriesDataframeOperation, AddSeriesDataframeOperation, RemoveSeriesDataframeOperation


@dataclass
class DataframeKeyError(KeyError):
    original_error: KeyError
    key: str
    dataframe: DataFrame

    def __str__(self):
        return str(self.original_error) + f"\n\nAvailable keys are: {list(self.dataframe.columns)}"


original_init = DataFrame.__init__
original_to_string = DataFrame.to_string
original_to_csv = DataFrame.to_csv
original_str = DataFrame.__str__
original_setitem = DataFrame.__setitem__
original_getitem = DataFrame.__getitem__
original_delitem = DataFrame.__delitem__


ORIGINAL_FLOAT_FORMAT = pd.get_option('display.float_format')
TO_CSV_FLOAT_FORMAT = ORIGINAL_FLOAT_FORMAT
STR_FLOAT_FORMAT = format_float


def _notify_on_change(self, operation: DataframeOperation):
    if ON_CHANGE.val is not None:
        ON_CHANGE.val(self, operation)


def __init__(self, *args, created_by: str = None, file_path: str = None, **kwargs):
    original_init(self, *args, **kwargs)
    self.created_by = created_by
    self.file_path = file_path
    _notify_on_change(self, CreationDataframeOperation(
        id=id(self), created_by=created_by, file_path=file_path, columns=list(self.columns.values)))


def __getitem__(self, key):
    try:
        return original_getitem(self, key)
    except KeyError as e:
        raise DataframeKeyError(original_error=e, key=key, dataframe=self)


def __setitem__(self, key, value):
    if hasattr(self, 'columns'):
        original_columns = self.columns
    else:
        original_columns = None
    original_setitem(self, key, value)
    if original_columns is not None:
        if isinstance(key, (list, tuple)):
            is_changing_existing_columns = any(k in original_columns for k in key)
        else:
            is_changing_existing_columns = key in original_columns
        operation_type = ChangeSeriesDataframeOperation if is_changing_existing_columns else AddSeriesDataframeOperation
        _notify_on_change(self, operation_type(id=id(self), series_name=key))


def __delitem__(self, key):
    original_delitem(self, key)
    _notify_on_change(self, RemoveSeriesDataframeOperation(id=id(self), series_name=key))


def __str__(self):
    # to avoid printing with [...] skipping columns
    return self.to_string()


def to_string(self, *args, **kwargs):
    """
    We print with short floats, avoid printing with [...] skipping columns, and checking which orientation to use.
    """
    current_float_format = pd.get_option('display.float_format')
    pd.set_option(f'display.float_format', STR_FLOAT_FORMAT)
    result1 = original_to_string(self, *args, **kwargs)
    result2 = original_to_string(self.T, *args, **kwargs)
    longest_line1 = max(len(line) for line in result1.split('\n'))
    longest_line2 = max(len(line) for line in result2.split('\n'))
    if longest_line1 > PDF_TEXT_WIDTH > longest_line2:
        result = result2
    else:
        result = result1
    pd.set_option(f'display.float_format', current_float_format)
    return result


def to_csv(self, *args, **kwargs):
    current_float_format = pd.get_option('display.float_format')
    pd.set_option(f'display.float_format', TO_CSV_FLOAT_FORMAT)
    result = original_to_csv(self, *args, **kwargs)
    pd.set_option(f'display.float_format', current_float_format)
    file_path = args[0] if len(args) > 0 else kwargs.get('path_or_buf')
    columns = list(self.columns.values) if hasattr(self, 'columns') else None
    _notify_on_change(self, SaveDataframeOperation(id=id(self), file_path=file_path, columns=columns))
    return result

