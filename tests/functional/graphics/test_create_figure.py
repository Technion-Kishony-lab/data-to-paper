import pytest
import os

from pathlib import Path

from data_to_paper.llm_coding_utils.df_to_figure import df_to_figure, \
    create_fig_for_df_to_figure_and_get_axis_parameters
from data_to_paper.utils.file_utils import run_in_directory


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
    # assert correct_fig.exists(), f"Correct figure {testname} does not exist."
    # assert modified_fig.exists(),  f"Figure {testname} was not created."
    # if correct_fig.read_bytes() != modified_fig.read_bytes():
    #     assert False, \
    #          f"Figures are different. If the new figure is correct, move it to correct_figures folder."
    # delete the modified figure if it is the same as the correct one
    # os.remove(modified_fig)


def test_single_series(name_of_test, test_data):
    create_fig_for_df_to_figure_and_get_axis_parameters(test_data, filepath=name_of_test, y='y')


def test_single_series_with_axis_labels(name_of_test, test_data):
    create_fig_for_df_to_figure_and_get_axis_parameters(test_data, filepath=name_of_test,
                                                        xlabel='X Axis Label', ylabel='Y Axis Label', y='y')


def test_plot_with_long_xtick_labels(name_of_test, test_data):
    test_data['x'] = ['This is a long label' for _ in range(10)]
    create_fig_for_df_to_figure_and_get_axis_parameters(test_data, filepath=name_of_test, y='y', x='x',
                                                        xlabel='X Axis Label', ylabel='Y Axis Label')


def test_plot_with_long_xtick_labels_wide_letters(name_of_test, test_data):
    test_data['x'] = ['WWWWWWWWWWWWWWWWWWWW' for _ in range(10)]
    create_fig_for_df_to_figure_and_get_axis_parameters(test_data, filepath=name_of_test, y='y', x='x',
                                                        xlabel='X Axis Label', ylabel='Y Axis Label')


def test_plot_with_yerr(name_of_test, test_data):
    create_fig_for_df_to_figure_and_get_axis_parameters(test_data, filepath=name_of_test, y='y', yerr='y_err')


def test_plot_with_y_ci(name_of_test, test_data):
    create_fig_for_df_to_figure_and_get_axis_parameters(test_data, filepath=name_of_test, y='y', y_ci='y_ci')


def test_plot_with_y_ci_low_high(name_of_test, test_data):
    create_fig_for_df_to_figure_and_get_axis_parameters(test_data, filepath=name_of_test, y='y',
                 y_ci=('y_ci_lower', 'y_ci_upper'))


def test_plot_with_y_p_value(name_of_test, test_data):
    create_fig_for_df_to_figure_and_get_axis_parameters(
        test_data, filepath=name_of_test, y='y', y_p_value='y_p_value', y_ci=('y_ci_lower', 'y_ci_upper'))


def test_plot_with_all_options_two_series(name_of_test, test_data):
    create_fig_for_df_to_figure_and_get_axis_parameters(test_data, filepath=name_of_test,
                 y=['y', 'y_2'], yerr=['y_err', 'y_err'],
                 y_p_value=['y_p_value', 'y_p_value'], kind='bar', xlabel='x')


def test_df_plot_with_pvalue_yerr(name_of_test, df_for_plot):
    create_fig_for_df_to_figure_and_get_axis_parameters(df_for_plot, filepath=name_of_test, y=['apples', 'oranges', 'bananas'],
                 yerr=['apples_err', 'oranges_err', 'bananas_err'],
                 y_p_value=['apples_p_value', 'oranges_p_value', 'bananas_p_value'])


def test_df_plot_with_pvalue_y_ci(name_of_test, df_for_plot):
    create_fig_for_df_to_figure_and_get_axis_parameters(df_for_plot, filepath=name_of_test, y=['apples', 'oranges', 'bananas'],
                 y_ci=['apples_ci', 'oranges_ci', 'bananas_ci'],
                 y_p_value=['apples_p_value', 'oranges_p_value', 'bananas_p_value'])


def test_plot_without_yerr_for_p_value(test_data):
    with pytest.raises(ValueError):
        create_fig_for_df_to_figure_and_get_axis_parameters(test_data, filepath='test', y='y', y_p_value='y_p_value')
