import pandas as pd
from pandas.core.frame import DataFrame

from scientistgpt.utils.mutable import Mutable
from scientistgpt.utils.singleton import run_once
from .dataframe_operations import SaveDataframeOperation, CreationDataframeOperation, DataframeOperation, \
    ChangeSeriesDataframeOperation, AddSeriesDataframeOperation, RemoveSeriesDataframeOperation

ON_CHANGE = Mutable(None)


original_init = DataFrame.__init__
original_to_csv = DataFrame.to_csv
original_str = DataFrame.__str__
original_setitem = DataFrame.__setitem__
original_delitem = DataFrame.__delitem__


def format_float(value: float):
    if value.is_integer():
        return str(int(value))
    else:
        return f'{value:.4g}'


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


def to_csv(self, *args, **kwargs):
    current_float_format = pd.get_option('display.float_format')
    pd.set_option(f'display.float_format', TO_CSV_FLOAT_FORMAT)
    result = original_to_csv(self, *args, **kwargs)
    pd.set_option(f'display.float_format', current_float_format)
    file_path = args[0] if len(args) > 0 else kwargs.get('path_or_buf')
    columns = list(self.columns.values) if hasattr(self, 'columns') else None
    _notify_on_change(self, SaveDataframeOperation(id=id(self), file_path=file_path, columns=columns))
    return result


def is_overriden(self):
    return True


FUNC_NAMES_TO_FUNCS = {
    '__init__': __init__,
    '__setitem__': __setitem__,
    '__delitem__': __delitem__,
    '__str__': __str__,
    'to_csv': to_csv,
}


@run_once
def override_core_ndframe():
    """
    Overrides the pandas DataFrame class to report changes in the data frame.
    """
    for func_name, func in FUNC_NAMES_TO_FUNCS.items():
        setattr(DataFrame, func_name, func)
    DataFrame.is_overriden = is_overriden

    if STR_FLOAT_FORMAT:
        pd.set_option(f'display.float_format', STR_FLOAT_FORMAT)
