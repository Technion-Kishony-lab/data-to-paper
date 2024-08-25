import pytest
import pandas as pd
import numpy as np
import os

from data_to_paper.llm_coding_utils.df_to_figure import df_to_figure
from data_to_paper.llm_coding_utils.df_plot_with_pvalue import df_plot_with_pvalue
from data_to_paper.utils.file_utils import run_in_directory


@pytest.fixture(scope="module")
def test_data():
    x = range(10)
    y = np.random.randn(10)
    y_2 = np.random.randn(10)
    y_err = np.random.rand(10) * 0.1
    y_ci_lower = y - np.random.rand(10) * 0.5
    y_ci_upper = y + np.random.rand(10) * 0.5
    y_p_value = np.random.rand(10) * 0.05
    df = pd.DataFrame({
        'x': x,
        'y': y,
        'y_2': y_2,
        'y_err': y_err,
        'y_ci_lower': y_ci_lower,
        'y_ci_upper': y_ci_upper,
        'y_p_value': y_p_value,
    })
    yield df


def test_basic_plot(test_data, tmpdir):
    df_plot_with_pvalue(test_data, y='y')


def test_plot_with_xlabel(test_data):
    df_plot_with_pvalue(test_data, xlabel='X Axis Label', y='y')


def test_plot_with_caption_and_label(test_data, tmpdir):
    with run_in_directory(tmpdir):
        df, filename = test_data
        df_to_figure(df, filename=filename, caption='Test Caption', label='fig:test')
        assert os.path.exists(filename)


def test_plot_with_note_and_glossary(test_data, tmpdir):
    with run_in_directory(tmpdir):
        df, filename = test_data
        note = 'This is a note.'
        glossary = {'y': 'Y-axis values'}
        df_to_figure(df, filename=filename, note=note, glossary=glossary)
        assert os.path.exists(filename)


def test_plot_with_yerr(test_data, tmpdir):
    with run_in_directory(tmpdir):
        df, filename = test_data
        df_to_figure(df, filename=filename, y='y', yerr='y_err')
        assert os.path.exists(filename)


def test_plot_with_y_ci(test_data, tmpdir):
    with run_in_directory(tmpdir):
        df, filename = test_data
        df_to_figure(df, filename=filename, y='y', y_ci=('y_ci_lower', 'y_ci_upper'))
        assert os.path.exists(filename)


def test_plot_with_y_p_value(test_data, tmpdir):
    with run_in_directory(tmpdir):
        df, filename = test_data
        df_to_figure(df, filename=filename, y='y', y_p_value='y_p_value', yerr='y_err')
        assert os.path.exists(filename)


def test_plot_with_all_options(test_data, tmpdir):
    with run_in_directory(tmpdir):
        df, filename = test_data
        df_to_figure(
            df, filename=filename, caption='Full options',
            label='fig:full_options', note='Note here', glossary={'x': 'X values', 'y': 'Y values'},
            xlabel='X Axis', ylabel='Y Axis', y='y', yerr='y_err', y_p_value='y_p_value'
        )
        assert os.path.exists(filename)


def test_plot_with_all_options_kind_scatter(test_data, tmpdir):
    with run_in_directory(tmpdir):
        df, filename = test_data
        df_to_figure(
            df, filename=filename, caption='Full options',
            label='fig:full_options', note='Note here', glossary={'x': 'X values', 'y': 'Y values'},
            xlabel='X Axis', ylabel='Y Axis', x='x', y='y', yerr='y_err', y_p_value='y_p_value', kind='scatter'
        )
        assert os.path.exists(filename)


def test_plot_with_all_options_kind_bar(test_data, tmpdir):
    with run_in_directory(tmpdir):
        df, filename = test_data
        df_to_figure(
            df, filename=filename, caption='Full options',
            label='fig:full_options', note='Note here', glossary={'x': 'X values', 'y': 'Y values'},
            y=['y', 'y_2'], yerr='y_err', y_p_value='y_p_value', kind='bar',
            xlabel='x',
        )
        assert os.path.exists(filename)


def test_plot_without_yerr_for_p_value(test_data, tmpdir):
    with run_in_directory(tmpdir):
        df, filename = test_data
        with pytest.raises(ValueError):
            df_to_figure(df, filename=filename, y='y', y_p_value='y_p_value')


def test_plot_with_multiple_columns_input(test_data, tmpdir):
    with run_in_directory(tmpdir):
        df, filename = test_data
        df_to_figure(df, filename=filename, y=['y', 'y_2'])
        assert os.path.exists(filename)


@pytest.fixture(scope="module")
def df_for_plot():
    data = {
        'apples': [3, 2, 5, 7, 2],
        'oranges': [1, 5, 3, 8, 6],
        'bananas': [3, 4, 2, 1, 5],
        'apples_err': [0.5, 4.3, 0.6, 0.2, 0.4],
        'oranges_err': [(0.3, 0.5), (0.4, 0.6), (0.5, 0.2), (0.1, 0.3), (0.3, 0.4)],
        'bananas_err': [0.2, 0.3, 0.1, 0.5, 0.4],
        'apples_ci': [(2.5, 3.5), (1.7, 2.3), (4.4, 5.6), (6.8, 7.2), (1.6, 2.4)],
        'oranges_ci': [(0.8, 1.2), (4.4, 5.6), (2.8, 3.2), (7.7, 8.3), (5.6, 6.4)],
        'bananas_ci': [(2.8, 3.2), (3.8, 4.2), (1.8, 2.2), (0.7, 1.3), (4.6, 5.4)],
        'apples_p_value': [0.1, 0.002, 0.3, 0.4, 0.5],
        'oranges_p_value': [0.1, 0.2, 0.001, 0.4, 0.5],
        'bananas_p_value': [0.1, 0.2, 0.3, 0.00001, 0.5]
    }
    df = pd.DataFrame(data)
    return df


def test_df_plot_with_pvalue_yerr(df_for_plot):
    df_plot_with_pvalue(df_for_plot, y=['apples', 'oranges', 'bananas'],
                        yerr=['apples_err', 'oranges_err', 'bananas_err'],
                        y_p_value=['apples_p_value', 'oranges_p_value', 'bananas_p_value'])


def test_df_plot_with_pvalue_y_ci(df_for_plot):
    df_plot_with_pvalue(df_for_plot, y=['apples', 'oranges', 'bananas'],
                        y_ci=['apples_ci', 'oranges_ci', 'bananas_ci'],
                        y_p_value=['apples_p_value', 'oranges_p_value', 'bananas_p_value'])
