import numpy as np
import pandas as pd
import pytest

from data_to_paper.run_gpt_code.overrides.dataframes.dataframe_operations import AddSeriesDataframeOperation
from data_to_paper.run_gpt_code.overrides.dataframes.df_methods.raise_on_call import UnAllowedDataframeMethodCall
from data_to_paper.run_gpt_code.overrides.dataframes.override_dataframe import TrackDataFrames
from data_to_paper.run_gpt_code.overrides.dataframes.utils import df_to_latex_with_value_format
from data_to_paper.utils.file_utils import run_in_directory


def test_track_dataframe_is_pickleable():
    import pickle
    pickle.dumps(TrackDataFrames())


def test_dataframe_allows_changing_when_not_in_context():
    with TrackDataFrames(allow_dataframes_to_change_existing_series=False) as tdf:
        df = pd.DataFrame({'a': [1, 2, 3]})
        df['a'] = [4, 5, 6]
    issues = tdf.issues
    assert len(issues) == 1
    msg = str(issues[0])
    assert '"a"' in msg
    assert "df['a'] = [4, 5, 6]" in msg

    df = pd.DataFrame({'a': [1, 2, 3]})
    df['a'] = [4, 5, 6]
    assert df['a'].tolist() == [4, 5, 6]


def test_dataframe_context_does_not_allow_changing_from_file_df(tmpdir_with_csv_file):
    with TrackDataFrames(allow_dataframes_to_change_existing_series=None) as tdf:
        df_denovo = pd.DataFrame({'a': [1, 2]})
        df_denovo['a'] = [4, 5]
        assert df_denovo['a'].tolist() == [4, 5]

        df_from_file = pd.read_csv(str(tmpdir_with_csv_file.join('test.csv')))
        df_from_file['a'] = [6, 7]
        assert df_from_file['a'].tolist() == [6, 7]

    issues = tdf.issues
    assert len(issues) == 1
    msg = str(issues[0])
    assert '"a"' in msg
    assert "df_denovo['a'] = [4, 5]" not in msg
    assert "df_from_file['a'] = [6, 7]" in msg


def test_dataframe_context_allows_changing(tmpdir_with_csv_file):
    with TrackDataFrames(allow_dataframes_to_change_existing_series=True):
        df = pd.read_csv(str(tmpdir_with_csv_file.join('test.csv')))
        df['a'] = [4, 5]
        assert df['a'].tolist() == [4, 5]


def test_dataframe_context_collects_changed_dataframes():
    with TrackDataFrames() as tdf:
        df = pd.DataFrame({'a': [1, 2, 3]})
        df['b'] = [4, 5, 6]
    dataframe_operations = tdf.dataframe_operations
    assert len(dataframe_operations) == 2
    assert dataframe_operations[1].series_name == 'b'


def test_dataframe_read_csv_creates_reporting_dataframe(tmpdir_with_csv_file):
    with TrackDataFrames() as tdf:
        pd.read_csv(str(tmpdir_with_csv_file.join('test.csv')))
    dataframe_operations = tdf.dataframe_operations
    assert len(dataframe_operations) == 1


def test_dataframe_creation_is_collected_upon_read_csv(tmpdir_with_csv_file):
    with TrackDataFrames() as tdf:
        pd.read_csv(str(tmpdir_with_csv_file.join('test.csv')))
    dataframe_operations = tdf.dataframe_operations
    assert len(dataframe_operations) == 1
    assert dataframe_operations[0].created_by == 'read_csv'
    assert dataframe_operations[0].filename == 'test.csv'


def test_dataframe_read_csv_is_collected_if_changed(tmpdir_with_csv_file):
    with TrackDataFrames() as tdf:
        df = pd.read_csv(str(tmpdir_with_csv_file.join('test.csv')))
        df['new'] = [4, 5]
    dataframe_operations = tdf.dataframe_operations
    assert len(dataframe_operations) == 2
    assert isinstance(dataframe_operations[1], AddSeriesDataframeOperation)
    assert dataframe_operations[1].series_name == 'new'


def test_dataframe_reports_save_csv(tmpdir_with_csv_file):
    with TrackDataFrames() as tdf:
        df = pd.read_csv(str(tmpdir_with_csv_file.join('test.csv')))
        df['new'] = [4, 5]
        df.to_csv(str(tmpdir_with_csv_file.join('test_modified.csv')))
    dataframe_operations = tdf.dataframe_operations
    assert len(dataframe_operations) == 4
    assert dataframe_operations[3].filename == 'test_modified.csv'


def test_get_changed_and_unsaved_dataframes(tmpdir_with_csv_file):
    with TrackDataFrames() as tdf:
        df = pd.read_csv(str(tmpdir_with_csv_file.join('test.csv')))
        df['new'] = [4, 5]
        dataframe_operations = tdf.dataframe_operations
        assert dataframe_operations.get_read_filenames_from_ids(
            dataframe_operations.get_read_changed_but_unsaved_ids()) == {'test.csv'}
        df.to_csv(str(tmpdir_with_csv_file.join('test_modified.csv')))
        assert len(dataframe_operations.get_read_changed_but_unsaved_ids()) == 0


def test_enforce_saving_changed_and_unsaved_dataframes(tmpdir_with_csv_file):
    with TrackDataFrames(enforce_saving_altered_dataframes=True) as tdf:
        df = pd.read_csv(str(tmpdir_with_csv_file.join('test.csv')))
        df['new'] = [4, 5]
        tdf.dataframe_operations
    assert 'test.cs' in tdf.issues[0].issue
    assert "doesn't save" in tdf.issues[0].issue


def test_dataframe_column_names(tmpdir_with_csv_file):
    with TrackDataFrames() as tdf:
        df = pd.read_csv(str(tmpdir_with_csv_file.join('test.csv')))
        df['new'] = [4, 5]
        df.to_csv(str(tmpdir_with_csv_file.join('test_modified.csv')))
    dataframe_operations = tdf.dataframe_operations
    assert np.array_equal(dataframe_operations[0].columns, ['a', 'b', 'c'])
    assert dataframe_operations[1].series_name == 'new'
    id_ = dataframe_operations[1].id
    assert np.array_equal(dataframe_operations.get_creation_columns(id_), ['a', 'b', 'c'])
    assert np.array_equal(dataframe_operations.get_save_columns(id_), ['a', 'b', 'c', 'new'])


def test_even_non_reporting_df_reports_on_save(tmpdir):
    with TrackDataFrames() as tdf:
        df = pd.concat([pd.Series([1, 2, 3]), pd.Series([4, 5, 6])])
        # set the column names:
        df = df.to_frame()
        df.columns = ['A']
        with run_in_directory(tmpdir):
            df.to_csv('test.csv')
    dataframe_operations = tdf.dataframe_operations
    assert len(dataframe_operations) == 3
    assert dataframe_operations[2].filename == 'test.csv'
    assert dataframe_operations[2].columns == ('A', )


def test_df_float_precision_to_csv():
    with TrackDataFrames():
        df = pd.DataFrame({'a': [1.23456789]})
        assert df.to_csv().strip().endswith('1.23456789')


def test_df_float_precision_str():
    with TrackDataFrames():
        df = pd.DataFrame({'a': [1.23456789]})
        assert str(df).endswith('1.235')


def test_df_float_precision_to_string():
    with TrackDataFrames():
        df = pd.DataFrame({'a': [1.23456789]})
        assert df.to_string().endswith('1.235')


def test_temporarily_change_float_format():
    with TrackDataFrames():
        df = pd.DataFrame({
            'single': [1.23456789, ],
            'two_values': ((1.23456789, 2.3456789), )})
        assert df.to_string().endswith('(1.235, 2.346)')


@pytest.mark.skip
def test_df_float_precision_of_mean_of_series():
    with TrackDataFrames():
        df = pd.DataFrame({'a': [1.23456789]})
        result = df["a"].mean()
        assert result == 1.23456789
        assert str(result).endswith('1.235')


def test_raise_on_call():
    with TrackDataFrames():
        df = pd.DataFrame()
        with pytest.raises(UnAllowedDataframeMethodCall) as exc:
            df.to_json()
    assert 'to_json' in str(exc.value)


def test_df_to_latex_with_value_format():
    with TrackDataFrames():
        df = pd.DataFrame({'a': [7.0, 1.2348]})
        latex = df_to_latex_with_value_format(df)
        assert '7 ' in latex
        assert '1.235 ' in latex


def test_df_raise_column_key_options():
    with TrackDataFrames():
        df = pd.DataFrame({'available_key': [7.0, 1.2385]})
        with pytest.raises(KeyError) as exc:
            df['b']
    assert 'available_key' in str(exc.value)


def test_df_raise_on_non_matching_index_in_setitem():
    with TrackDataFrames():
        df = pd.DataFrame({'a': [1, 2]}, index=['x', 'y'])
        df['b'] = [3, 4]
        df['c'] = pd.Series([5, 6], index=['x', 'y'])
        with pytest.raises(ValueError) as exc:
            df['d'] = pd.Series([7, 8], index=['x', 'z'])
    assert "['x', 'y']" in str(exc.value)
    assert "['x', 'z']" in str(exc.value)


def test_loc_key_options():
    with TrackDataFrames():
        df = pd.DataFrame(pd.DataFrame({
            'col_A': [1, 2, 3],
            'col_B': [4, 5, 6]
        }, index=['row_x', 'row_y', 'row_z']))
        with pytest.raises(KeyError) as exc:
            df.loc['row', 'col']
    e = exc.value
    assert 'col_A' in str(e)
    assert 'col_B' in str(e)
    assert 'row_x' in str(e)
    assert 'row_y' in str(e)
    assert 'row_z' in str(e)
