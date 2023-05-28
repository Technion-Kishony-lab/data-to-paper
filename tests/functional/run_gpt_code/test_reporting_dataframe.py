import pandas as pd
import pytest

from scientistgpt.run_gpt_code.overrides.override_dataframe import hook_dataframe, ReportingDataFrame, \
    collect_created_and_changed_data_frames, DataFrameSeriesChange, SeriesOperationType


@pytest.fixture()
def tmpdir_with_csv_file(tmpdir):
    csv_file = tmpdir.join('test.csv')
    csv_file.write('a,b,c\n1,2,3\n4,5,6')
    return tmpdir


def test_dataframe_allows_changing_when_not_in_context():
    hook_dataframe()

    df = pd.DataFrame({'a': [1, 2, 3]})
    assert type(df) is ReportingDataFrame
    df['a'] = [4, 5, 6]
    assert df['a'].tolist() == [4, 5, 6]


def test_dataframe_allows_adding_when_not_in_context():
    hook_dataframe()
    df2 = pd.DataFrame({'a': [1, 2, 3]})
    df2['b'] = [4, 5, 6]
    assert 'b' in df2


def test_dataframe_context_does_not_allow_changing():
    with collect_created_and_changed_data_frames(allow_changing_existing_series=False):
        df = pd.DataFrame({'a': [1, 2, 3]})
        assert type(df) is ReportingDataFrame
        with pytest.raises(DataFrameSeriesChange):
            df['a'] = [4, 5, 6]


def test_dataframe_context_allows_changing():
    with collect_created_and_changed_data_frames(allow_changing_existing_series=True):
        df = pd.DataFrame({'a': [1, 2, 3]})
        assert type(df) is ReportingDataFrame
        df['a'] = [4, 5, 6]
        assert df['a'].tolist() == [4, 5, 6]


def test_dataframe_context_collects_changed_dataframes():
    with collect_created_and_changed_data_frames() as dataframe_operations:
        df = pd.DataFrame({'a': [1, 2, 3]})
        df['b'] = [4, 5, 6]
    assert len(dataframe_operations) == 2
    print(dataframe_operations)
    assert dataframe_operations[1].series_name == 'b'


def test_dataframe_read_csv_creates_reporting_dataframe(tmpdir_with_csv_file):
    with collect_created_and_changed_data_frames():
        df = pd.read_csv(str(tmpdir_with_csv_file.join('test.csv')))
    assert type(df) is ReportingDataFrame


def test_dataframe_creation_is_collected_upon_read_csv(tmpdir_with_csv_file):
    with collect_created_and_changed_data_frames() as dataframe_operations:
        pd.read_csv(str(tmpdir_with_csv_file.join('test.csv')))
    assert len(dataframe_operations) == 1
    assert dataframe_operations[0].created_by == 'read_csv'
    assert dataframe_operations[0].filename == 'test.csv'


def test_dataframe_read_csv_is_collected_if_changed(tmpdir_with_csv_file):
    with collect_created_and_changed_data_frames() as changed_data_frames:
        df = pd.read_csv(str(tmpdir_with_csv_file.join('test.csv')))
        df['new'] = [4, 5]
    assert len(changed_data_frames) == 2
    assert changed_data_frames[1].operation_type == SeriesOperationType.ADD
