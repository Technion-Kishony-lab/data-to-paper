import pandas as pd
import pytest

from scientistgpt.run_gpt_code.overrides.override_dataframe import hook_dataframe, ChangeReportingDataFrame, \
    collect_changed_data_frames, DataFrameSeriesChange


@pytest.fixture()
def tmpdir_with_csv_file(tmpdir):
    csv_file = tmpdir.join('test.csv')
    csv_file.write('a,b,c\n1,2,3\n4,5,6')
    return tmpdir


def test_dataframe_allows_changing_when_not_in_context():
    hook_dataframe()

    df = pd.DataFrame({'a': [1, 2, 3]})
    assert type(df) is ChangeReportingDataFrame
    df['a'] = [4, 5, 6]
    assert df['a'].tolist() == [4, 5, 6]


def test_dataframe_allows_adding_when_not_in_context():
    hook_dataframe()
    df2 = pd.DataFrame({'a': [1, 2, 3]})
    df2['b'] = [4, 5, 6]
    assert 'b' in df2


def test_dataframe_context_does_not_allow_changing():
    with collect_changed_data_frames(allow_changing_existing_series=False):
        df = pd.DataFrame({'a': [1, 2, 3]})
        assert type(df) is ChangeReportingDataFrame
        with pytest.raises(DataFrameSeriesChange):
            df['a'] = [4, 5, 6]


def test_dataframe_context_allows_changing():
    with collect_changed_data_frames(allow_changing_existing_series=True):
        df = pd.DataFrame({'a': [1, 2, 3]})
        assert type(df) is ChangeReportingDataFrame
        df['a'] = [4, 5, 6]
        assert df['a'].tolist() == [4, 5, 6]


def test_dataframe_context_collects_changed_dataframes():
    with collect_changed_data_frames() as changed_data_frames:
        df = pd.DataFrame({'a': [1, 2, 3]})
        df['b'] = [4, 5, 6]
    assert len(changed_data_frames) == 1
    assert changed_data_frames[0]['b'].tolist() == [4, 5, 6]


def test_dataframe_read_csv_creates_reporting_dataframe(tmpdir_with_csv_file):
    with collect_changed_data_frames():
        df = pd.read_csv(str(tmpdir_with_csv_file.join('test.csv')))
    assert type(df) is ChangeReportingDataFrame


def test_dataframe_read_csv_is_not_collected_if_did_not_changed(tmpdir_with_csv_file):
    with collect_changed_data_frames() as changed_data_frames:
        pd.read_csv(str(tmpdir_with_csv_file.join('test.csv')))
    assert len(changed_data_frames) == 0


def test_dataframe_read_csv_is_collected_if_changed(tmpdir_with_csv_file):
    with collect_changed_data_frames() as changed_data_frames:
        df = pd.read_csv(str(tmpdir_with_csv_file.join('test.csv')))
        df['new'] = [4, 5]
    assert len(changed_data_frames) == 1
    assert changed_data_frames[0]['new'].tolist() == [4, 5]
