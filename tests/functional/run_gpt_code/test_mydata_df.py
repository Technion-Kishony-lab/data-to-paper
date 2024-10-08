import os

import pandas as pd

from data_to_paper.run_gpt_code.overrides.dataframes import TrackDataFrames
from data_to_paper.run_gpt_code.overrides.dataframes.df_with_attrs import InfoDataFrame
import pickle


def test_extra_info_df(tmpdir):
    os.chdir(tmpdir)
    df = InfoDataFrame({'a': [1, 2]}, extra_info=(7, 'ok'))

    with open('custom_df.pickle', 'wb') as file:
        pickle.dump(df, file)

    with open('custom_df.pickle', 'rb') as file:
        loaded_df = pickle.load(file)
    assert type(loaded_df) is InfoDataFrame
    assert loaded_df.extra_info == (7, 'ok')


def test_extra_info_df_with_pd_to_pickle(tmpdir):
    os.chdir(tmpdir)
    df = InfoDataFrame({'a': [1, 2]}, extra_info=(7, 'ok'))

    df.to_pickle('custom_df_pd.pickle')

    loaded_df = pd.read_pickle('custom_df_pd.pickle')
    assert type(loaded_df) is InfoDataFrame
    assert loaded_df.extra_info == (7, 'ok')


def test_extra_info_df_with_pd_to_pickle_under_track_df_context(tmpdir):
    os.chdir(tmpdir)
    df = InfoDataFrame({'a': [1, 2]}, extra_info=(7, 'ok'))

    with TrackDataFrames():
        df.to_pickle('custom_df_pd.pickle')
        loaded_df = pd.read_pickle('custom_df_pd.pickle')
    assert type(loaded_df) is InfoDataFrame
    assert loaded_df.extra_info == (7, 'ok')


def test_extra_info_df_transpose(tmpdir):
    os.chdir(tmpdir)
    df = InfoDataFrame({'a': [1, 2]}, extra_info=(7, 'ok'))
    assert df.columns.tolist() == ['a']

    df = df.T
    assert df.index.tolist() == ['a']
    assert df.extra_info == (7, 'ok')
    assert type(df) is InfoDataFrame
