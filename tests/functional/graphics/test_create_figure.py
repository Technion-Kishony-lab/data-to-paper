import pytest
import pandas as pd
import numpy as np
import os

from data_to_paper.research_types.hypothesis_testing.coding.original_utils import to_figure_with_note
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
    filename = 'test_figure.tex'
    yield df, filename


def test_basic_plot(test_data, tmpdir):
    with run_in_directory(tmpdir):
        df, filename = test_data
        to_figure_with_note(df, filename=filename)
        assert os.path.exists(filename)


def test_plot_with_xlabel(test_data, tmpdir):
    with run_in_directory(tmpdir):
        df, filename = test_data
        to_figure_with_note(df, filename=filename, xlabel='X Axis Label')
        assert os.path.exists(filename)


def test_plot_with_ylabel(test_data, tmpdir):
    with run_in_directory(tmpdir):
        df, filename = test_data
        to_figure_with_note(df, filename=filename, ylabel='Y Axis Label')
        assert os.path.exists(filename)


def test_plot_with_caption_and_label(test_data, tmpdir):
    with run_in_directory(tmpdir):
        df, filename = test_data
        to_figure_with_note(df, filename=filename, caption='Test Caption', label='fig:test')
        assert os.path.exists(filename)


def test_plot_with_note_and_glossary(test_data, tmpdir):
    with run_in_directory(tmpdir):
        df, filename = test_data
        note = 'This is a note.'
        glossary = {'y': 'Y-axis values'}
        to_figure_with_note(df, filename=filename, note=note, glossary=glossary)
        assert os.path.exists(filename)


def test_plot_with_yerr(test_data, tmpdir):
    with run_in_directory(tmpdir):
        df, filename = test_data
        to_figure_with_note(df, filename=filename, y='y', yerr='y_err')
        assert os.path.exists(filename)


def test_plot_with_y_ci(test_data, tmpdir):
    with run_in_directory(tmpdir):
        df, filename = test_data
        to_figure_with_note(df, filename=filename, y='y', y_ci=('y_ci_lower', 'y_ci_upper'))
        assert os.path.exists(filename)


def test_plot_with_y_p_value(test_data, tmpdir):
    with run_in_directory(tmpdir):
        df, filename = test_data
        to_figure_with_note(df, filename=filename, y='y', y_p_value='y_p_value', yerr='y_err')
        assert os.path.exists(filename)


def test_plot_with_all_options(test_data, tmpdir):
    with run_in_directory(tmpdir):
        df, filename = test_data
        to_figure_with_note(
            df, filename=filename, caption='Full options',
            label='fig:full_options', note='Note here', glossary={'x': 'X values', 'y': 'Y values'},
            xlabel='X Axis', ylabel='Y Axis', y='y', yerr='y_err', y_p_value='y_p_value'
        )
        assert os.path.exists(filename)


def test_plot_with_all_options_kind_scatter(test_data, tmpdir):
    with run_in_directory(tmpdir):
        df, filename = test_data
        to_figure_with_note(
            df, filename=filename, caption='Full options',
            label='fig:full_options', note='Note here', glossary={'x': 'X values', 'y': 'Y values'},
            xlabel='X Axis', ylabel='Y Axis', x='x', y='y', yerr='y_err', y_p_value='y_p_value', kind='scatter'
        )
        assert os.path.exists(filename)


def test_plot_with_all_options_kind_bar(test_data, tmpdir):
    with run_in_directory(tmpdir):
        df, filename = test_data
        to_figure_with_note(
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
            to_figure_with_note(df, filename=filename, y='y', y_p_value='y_p_value')


def test_plot_with_multiple_columns_input(test_data, tmpdir):
    with run_in_directory(tmpdir):
        df, filename = test_data
        to_figure_with_note(df, filename=filename, y=['y', 'y_2'])
        assert os.path.exists(filename)
