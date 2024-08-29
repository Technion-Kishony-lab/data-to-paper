from typing import Dict, Any, Optional

from pathlib import Path

from data_to_paper.run_gpt_code.overrides.contexts import OverrideStatisticsPackages
from data_to_paper.run_gpt_code.overrides.dataframes import TrackDataFrames


def create_pandas_and_stats_contexts(allow_dataframes_to_change_existing_series: Optional[bool] = False,
                                     enforce_saving_altered_dataframes: bool = False,
                                     issue_if_statistics_test_not_called: bool = False,
                                     ) -> Dict[str, Any]:
    return {
        'TrackDataFrames': TrackDataFrames(
            allow_dataframes_to_change_existing_series=allow_dataframes_to_change_existing_series,
            enforce_saving_altered_dataframes=enforce_saving_altered_dataframes,
        ),
        'OverrideStatisticsPackages': OverrideStatisticsPackages(
            issue_if_statistics_test_not_called=issue_if_statistics_test_not_called),
    }


def convert_filename_to_label(filename, label) -> str:
    """
    Convert a filename to a label.
    """
    if label:
        raise ValueError(f'Do not provide the `label` argument. The label is derived from the filename.')
    if not filename:
        return ''
    label = Path(filename).stem
    ext = Path(filename).suffix
    if ext:
        raise ValueError(f'Invalid filename: "{filename}". The filename must not have an extension.')

    # check if the label is valid:
    if not label.isidentifier():
        raise ValueError(f'Invalid filename: "{filename}". The filename must be a valid identifier.')
    label = label.replace('_', '-')
    return label
