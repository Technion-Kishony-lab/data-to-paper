import pandas as pd
import pytest

from data_to_paper.run_gpt_code.overrides.dataframes.dataframe_operations import AddSeriesDataframeOperation
from data_to_paper.run_gpt_code.overrides.dataframes.df_methods.raise_on_call import UnAllowedDataframeMethodCall
from data_to_paper.run_gpt_code.overrides.dataframes.override_dataframe import hook_dataframe_creating_funcs, \
    collect_created_and_changed_data_frames, DataFrameSeriesChange
from data_to_paper.utils.file_utils import run_in_directory


def test_dataframe_allows_changing_when_not_in_context():
    hook_dataframe_creating_funcs()

    df = pd.DataFrame({'a': [1, 2, 3]})
    df['a'] = [4, 5, 6]
    assert df['a'].tolist() == [4, 5, 6]


def test_dataframe_allows_adding_when_not_in_context():
    hook_dataframe_creating_funcs()
    df2 = pd.DataFrame({'a': [1, 2, 3]})
    df2['b'] = [4, 5, 6]
    assert 'b' in df2


def test_dataframe_context_does_not_allow_changing(tmpdir_with_csv_file):
    with collect_created_and_changed_data_frames(allow_changing_existing_series=False):
        df = pd.read_csv(str(tmpdir_with_csv_file.join('test.csv')))
        with pytest.raises(DataFrameSeriesChange):
            df['a'] = [4, 5]


def test_dataframe_context_allows_changing():
    with collect_created_and_changed_data_frames(allow_changing_existing_series=True):
        df = pd.DataFrame({'a': [1, 2, 3]})
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
    with collect_created_and_changed_data_frames() as dataframe_operations:
        pd.read_csv(str(tmpdir_with_csv_file.join('test.csv')))
    assert len(dataframe_operations) == 1


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
    assert isinstance(changed_data_frames[1], AddSeriesDataframeOperation)
    assert changed_data_frames[1].series_name == 'new'


def test_dataframe_reports_save_csv(tmpdir_with_csv_file):
    with collect_created_and_changed_data_frames() as changed_data_frames:
        df = pd.read_csv(str(tmpdir_with_csv_file.join('test.csv')))
        df['new'] = [4, 5]
        df.to_csv(str(tmpdir_with_csv_file.join('test_modified.csv')))
    assert len(changed_data_frames) == 4
    assert changed_data_frames[3].filename == 'test_modified.csv'


def test_get_changed_and_unsaved_dataframes(tmpdir_with_csv_file):
    with collect_created_and_changed_data_frames() as dataframe_operations:
        df = pd.read_csv(str(tmpdir_with_csv_file.join('test.csv')))
        df['new'] = [4, 5]
        assert dataframe_operations.get_read_filenames_from_ids(
            dataframe_operations.get_read_changed_but_unsaved_ids()) == {'test.csv'}
        df.to_csv(str(tmpdir_with_csv_file.join('test_modified.csv')))
        assert len(dataframe_operations.get_read_changed_but_unsaved_ids()) == 0


def test_dataframe_column_names(tmpdir_with_csv_file):
    with collect_created_and_changed_data_frames() as dataframe_operations:
        df = pd.read_csv(str(tmpdir_with_csv_file.join('test.csv')))
        df['new'] = [4, 5]
        df.to_csv(str(tmpdir_with_csv_file.join('test_modified.csv')))
    assert dataframe_operations[0].columns == ['a', 'b', 'c']
    assert dataframe_operations[1].series_name == 'new'
    id_ = dataframe_operations[1].id
    assert dataframe_operations.get_creation_columns(id_) == ['a', 'b', 'c']
    assert dataframe_operations.get_save_columns(id_) == ['a', 'b', 'c', 'new']


def test_even_non_reporting_df_reports_on_save(tmpdir):
    with collect_created_and_changed_data_frames() as dataframe_operations:
        df = pd.concat([pd.Series([1, 2, 3]), pd.Series([4, 5, 6])])
        # set the column names:
        df = df.to_frame()
        df.columns = ['A']
        with run_in_directory(tmpdir):
            df.to_csv('test.csv')

    assert len(dataframe_operations) == 3
    assert dataframe_operations[2].filename == 'test.csv'
    assert dataframe_operations[2].columns == ['A']


def test_df_float_precision_to_csv():
    with collect_created_and_changed_data_frames():
        df = pd.DataFrame({'a': [1.23456789]})
        assert df.to_csv().endswith('1.23456789\n')


def test_df_float_precision_str():
    with collect_created_and_changed_data_frames():
        df = pd.DataFrame({'a': [1.23456789]})
        assert str(df).endswith('1.235')


def test_df_float_precision_to_string():
    with collect_created_and_changed_data_frames():
        df = pd.DataFrame({'a': [1.23456789]})
        assert df.to_string().endswith('1.235')


@pytest.mark.skip
def test_df_float_precision_of_mean_of_series():
    with collect_created_and_changed_data_frames():
        df = pd.DataFrame({'a': [1.23456789]})
        result = df["a"].mean()
        assert result == 1.23456789
        assert str(result).endswith('1.235')


def test_raise_on_call():
    with collect_created_and_changed_data_frames():
        df = pd.DataFrame()
        with pytest.raises(UnAllowedDataframeMethodCall) as exc:
            df.to_html()
    assert 'to_html' in str(exc.value)
