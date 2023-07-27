from functools import partial

import pandas as pd

from contextlib import contextmanager
from dataclasses import dataclass

from data_to_paper.utils.singleton import run_once
from .dataframe_operations import DataframeOperation, ChangeSeriesDataframeOperation, DataframeOperations
from .on_change import ON_CHANGE
from .overridde_core import override_core_ndframe


@dataclass
class DataFrameSeriesChange(Exception):
    """
    Exception that is raised when a data frame series is changed.
    """
    changed_series: str = None

    def __str__(self):
        return f'Changed series: {self.changed_series}'


DF_CREATING_FUNCTIONS = [
    'read_csv',
    'read_excel',
    'read_json',
]


def hook_func(*args, original_func=None, **kwargs):
    with ON_CHANGE.temporary_set(None):
        df = original_func(*args, **kwargs)
    file_path = args[0] if len(args) > 0 else kwargs.get('filepath_or_buffer')
    reporting_df = pd.DataFrame(df, created_by=original_func.__name__, file_path=file_path)
    return reporting_df


@run_once
def hook_dataframe_creating_funcs():
    """
    Hook all the dataframe creating functions so that they return a ReportingDataFrame instance.
    """
    for func_name in DF_CREATING_FUNCTIONS:
        original_func = getattr(pd, func_name)
        setattr(pd, func_name, partial(hook_func, original_func=original_func))


@contextmanager
def collect_created_and_changed_data_frames(allow_changing_existing_series=True) -> DataframeOperations:
    """
    Context manager that collects all the data frames that are created and their changes during the context.
    """
    hook_dataframe_creating_funcs()
    override_core_ndframe()
    dataframe_operations = DataframeOperations()

    def on_change(df, series_operation: DataframeOperation):
        if isinstance(series_operation, ChangeSeriesDataframeOperation) \
                and not allow_changing_existing_series \
                and df.file_path is not None:
            raise DataFrameSeriesChange(changed_series=series_operation.series_name)
        dataframe_operations.append(series_operation)

    with ON_CHANGE.temporary_set(on_change):
        yield dataframe_operations

    #
    # if not self.ALLOW_CHANGING_EXISTING_SERIES and operation_type is ChangeSeriesDataframeOperation:
    #     raise DataFrameSeriesChange(changed_series=key)
