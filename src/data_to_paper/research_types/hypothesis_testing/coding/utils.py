from typing import Dict, Any

from data_to_paper.run_gpt_code.overrides.contexts import OverrideStatisticsPackages
from data_to_paper.run_gpt_code.overrides.dataframes import TrackDataFrames


def get_additional_contexts(allow_dataframes_to_change_existing_series: bool = False,
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
