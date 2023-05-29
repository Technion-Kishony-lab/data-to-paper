from scientistgpt.utils.singleton import run_once
from pandas.core.generic import NDFrame
from .dataframe_operations import SaveDataframeOperation

original_to_csv = NDFrame.to_csv
original_str = NDFrame.__str__


def to_csv(self, *args, **kwargs):
    from .override_dataframe import ReportingDataFrame
    on_change = ReportingDataFrame.ON_CHANGE
    result = original_to_csv(self, *args, **kwargs)
    if on_change is not None:
        file_path = args[0] if len(args) > 0 else kwargs.get('path_or_buf')
        columns = list(self.columns.values) if hasattr(self, 'columns') else None
        on_change(self, SaveDataframeOperation(id=id(self), file_path=file_path, columns=columns))
    return result


def __str__(self):
    # to avoid printing with [...] skipping columns
    return self.to_string()


@run_once
def override_core_ndframe():
    """
    Overrides the pandas DataFrame class to report changes in the data frame.
    """
    NDFrame.__str__ = __str__
    NDFrame.to_csv = to_csv
