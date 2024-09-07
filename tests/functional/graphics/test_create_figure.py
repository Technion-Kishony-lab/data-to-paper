from functools import partial

import pytest
import pandas as pd
import numpy as np
import os

from pathlib import Path

from data_to_paper.llm_coding_utils.df_to_figure import df_to_figure
from data_to_paper.utils.file_utils import run_in_directory


df_to_figure = partial(df_to_figure, create_fig=True)


CORRECT_FIGURES_FOLDER = Path(__file__).parent / 'correct_figures'
MODIFIED_FIGURES_FOLDER = Path(__file__).parent / 'modified_figures'


# Define a fixture that returns the current test name
@pytest.fixture
def name_of_test(request, tmpdir):
    testname = request.node.name

    if not MODIFIED_FIGURES_FOLDER.exists():
        MODIFIED_FIGURES_FOLDER.mkdir()
    if not CORRECT_FIGURES_FOLDER.exists():
        CORRECT_FIGURES_FOLDER.mkdir()
    with run_in_directory(MODIFIED_FIGURES_FOLDER):
        yield testname

    # check if the figures are the same:
    correct_fig = CORRECT_FIGURES_FOLDER / (testname + '.png')
    modified_fig = MODIFIED_FIGURES_FOLDER / (testname + '.png')
    assert correct_fig.exists(), f"Correct figure {testname} does not exist."
    assert modified_fig.exists(),  f"Figure {testname} was not created."
    if correct_fig.read_bytes() != modified_fig.read_bytes():
        assert False, \
            f"Figures are different. If the new figure is correct, move it to correct_figures folder."
    # delete the modified figure if it is the same as the correct one
    os.remove(modified_fig)


@pytest.fixture(scope="module")
def test_data():
    x = range(10)
    np.random.seed(0)
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
        'y_ci': list(zip(y_ci_lower, y_ci_upper)),
        'y_p_value': y_p_value,
    })
    yield df


def test_basic_plot(name_of_test, test_data):
    df_to_figure(test_data, filename=name_of_test, y='y')


def test_plot_with_xlabel(name_of_test, test_data):
    df_to_figure(test_data, filename=name_of_test, xlabel='X Axis Label', y='y')


def test_plot_with_caption_and_label(name_of_test, test_data):
    latex = df_to_figure(test_data, filename=name_of_test, caption='Test Caption', y='y')
    assert "df.plot(y='y')" in latex
    assert os.path.exists(name_of_test + '.png')


def test_plot_with_long_xtick_labels(name_of_test, test_data):
    test_data['x'] = ['This is a long label' for _ in range(10)]
    df_to_figure(test_data, filename=name_of_test, y='y')
    assert os.path.exists(name_of_test + '.png')


def test_plot_with_note_and_glossary(name_of_test, test_data):
    note = 'This is a note.'
    glossary = {'y': 'Y-axis values'}
    latex = df_to_figure(test_data, filename=name_of_test, note=note, glossary=glossary, y='y')
    assert "df.plot(y='y')" in latex
    assert "y: Y-axis values" in latex
    assert os.path.exists(name_of_test + '.png')


def test_plot_with_yerr(name_of_test, test_data):
    df_to_figure(test_data, filename=name_of_test, y='y', yerr='y_err')
    assert os.path.exists(name_of_test + '.png')


def test_plot_with_y_ci(name_of_test, test_data):
    df_to_figure(test_data, filename=name_of_test, y='y', y_ci='y_ci')
    assert os.path.exists(name_of_test + '.png')


def test_plot_with_y_ci_low_high(name_of_test, test_data):
    df_to_figure(test_data, filename=name_of_test, y='y',
                 y_ci=('y_ci_lower', 'y_ci_upper'))
    assert os.path.exists(name_of_test + '.png')


def test_plot_with_y_p_value(name_of_test, test_data):
    df_to_figure(test_data, filename=name_of_test, y='y', y_p_value='y_p_value',
                 yerr='y_err')
    assert os.path.exists(name_of_test + '.png')


def test_plot_with_all_options(name_of_test, test_data):
    df_to_figure(test_data, filename=name_of_test, caption='Full options', note='Note here',
                 glossary={'x': 'X values', 'y': 'Y values'}, xlabel='X Axis', ylabel='Y Axis', y='y', yerr='y_err',
                 y_p_value='y_p_value')
    assert os.path.exists(name_of_test + '.png')


def test_plot_with_all_options_kind_scatter(name_of_test, test_data):
    df_to_figure(test_data, filename=name_of_test, caption='Full options', note='Note here',
                 glossary={'x': 'X values', 'y': 'Y values'}, xlabel='X Axis', ylabel='Y Axis', x='x', y='y',
                 yerr='y_err', y_p_value='y_p_value', kind='bar')
    assert os.path.exists(name_of_test + '.png')


def test_plot_with_all_options_kind_bar(name_of_test, test_data):
    df_to_figure(test_data, filename=name_of_test, caption='Full options', note='Note here',
                 glossary={'x': 'X values', 'y': 'Y values'}, y=['y', 'y_2'], yerr=['y_err', 'y_err'],
                 y_p_value=['y_p_value', 'y_p_value'], kind='bar', xlabel='x')
    assert os.path.exists(name_of_test + '.png')


def test_plot_without_yerr_for_p_value(test_data):
    with pytest.raises(ValueError):
        df_to_figure(test_data, filename='test', y='y', y_p_value='y_p_value')


def test_plot_with_multiple_columns_input(name_of_test, test_data):
    df_to_figure(test_data, filename=name_of_test, y=['y', 'y_2'])
    assert os.path.exists(name_of_test + '.png')


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


def test_df_plot_with_pvalue_yerr(name_of_test, df_for_plot):
    df_to_figure(df_for_plot, filename=name_of_test, y=['apples', 'oranges', 'bananas'],
                 yerr=['apples_err', 'oranges_err', 'bananas_err'],
                 y_p_value=['apples_p_value', 'oranges_p_value', 'bananas_p_value'])


def test_df_plot_with_pvalue_y_ci(name_of_test, df_for_plot):
    df_to_figure(df_for_plot, filename=name_of_test, y=['apples', 'oranges', 'bananas'],
                 y_ci=['apples_ci', 'oranges_ci', 'bananas_ci'],
                 y_p_value=['apples_p_value', 'oranges_p_value', 'bananas_p_value'])
