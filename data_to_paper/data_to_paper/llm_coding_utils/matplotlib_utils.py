from dataclasses import dataclass
from typing import Tuple, Optional, Dict, List, Union

from matplotlib import pyplot as plt
from .consts import FIG_SIZE_INCHES

def get_xy_coordinates_of_df_plot(df, x=None, y=None, kind='line') -> Dict[int, Dict[int, Tuple[float, float]]]:
    """
    Plots the DataFrame and retrieves x and y coordinates for each data point.
    Returns a dictionary of dictionaries, where the first key is the column index and the second key is the row index.
    """
    # Create the plot
    ax = df.plot(x=x, y=y, kind=kind, legend=False)

    coords = {}
    if kind == 'bar':
        # Handle bar plots
        for col_index, container in enumerate(ax.containers):
            coords[col_index] = {}
            for rect, row_index in zip(container, range(len(df))):
                coords[col_index][row_index] = (rect.get_x() + rect.get_width() / 2, rect.get_height())
    else:
        # Handle line and other plots
        for line, col_index in zip(ax.lines, range(len(df.columns))):
            coords[col_index] = {}
            for x_val, y_val, row_index in zip(line.get_xdata(), line.get_ydata(), range(len(df))):
                coords[col_index][row_index] = (x_val, y_val)

    plt.close()  # Close the plot to avoid display
    return coords


def are_axes_numeric(ax: plt.Axes) -> Tuple[bool, bool]:
    """
    For each axes, x and y, check if all the ticks are numeric.
    """
    def is_numeric(tick):
        tick = tick.get_text()
        if isinstance(tick, (int, float)):
            return True
        try:
            float(tick)
            return True
        except ValueError:
            return False

    return all(is_numeric(tick) for tick in ax.get_xticklabels()), \
        all(is_numeric(tick) for tick in ax.get_yticklabels())


def replace_singleton_legend_with_axis_label(ax: plt.Axes, kind: str) -> Optional[str]:
    """
    Replace a singleton legend with an axis label.
    """
    # suppress all warnings that are not errors:
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        legend = ax.legend(handlelength=0.75, handleheight=0.75, handletextpad=0.5, borderpad=.25,  borderaxespad=0.,
                           labelspacing=0.3, framealpha=0, bbox_to_anchor=(1.05, 0.5), loc='center left',
                           bbox_transform=ax.transAxes)
    RelativeFigHeigth=FIG_SIZE_INCHES[1]/ax.figure.get_size_inches()[1]
    legend_keys = [text.get_text() for text in legend.get_texts()]
    is_singleton = len(legend_keys) == 1
    if not is_singleton:
        legend.set_bbox_to_anchor((1.05, 0.5))
        ax.set_position([0.1, 0.15+0.8*(1-RelativeFigHeigth), 0.5, 0.8*(RelativeFigHeigth)]) # shift plot to left to accomodate for label
        for text in legend.get_texts():
            text.set_fontsize(9)
        return
    singleton_legend_key = legend_keys[0]
    if kind == 'barh':
        # Horizontal bar plot. The legend is the x-axis label.
        if ax.get_xlabel() == '':
            ax.set_xlabel(singleton_legend_key)
    else:
        # Normal plot. The legend is the y-axis label.
        if ax.get_ylabel() == '':
            ax.set_ylabel(singleton_legend_key)
    legend.remove()
    ax.set_position([.25, 0.15+0.8*(1-RelativeFigHeigth), 0.5, 0.8*RelativeFigHeigth]) # center plot
    return singleton_legend_key


def add_grid_line_at_base_if_needed(ax: plt.Axes, h_or_v: str, color: str = 'black', linewidth: int = 1,
                                    linestyle: str = '--'):
    """
    Add a grid line at zero, if zero is within the axis limits.
    h_or_v: 'h' for horizontal, 'v' for vertical, 'hv' for both.
    """
    if 'h' in h_or_v:
        base_value = 1 if ax.get_yscale() == 'log' else 0
        if ax.get_ylim()[0] < base_value < ax.get_ylim()[1]:
            ax.axhline(base_value, color=color, linewidth=linewidth, linestyle=linestyle)
    if 'v' in h_or_v:
        base_value = 1 if ax.get_xscale() == 'log' else 0
        if ax.get_xlim()[0] < base_value < ax.get_xlim()[1]:
            ax.axvline(base_value, color=color, linewidth=linewidth, linestyle=linestyle)


def rotate_xticklabels_if_not_numeric(ax: plt.Axes):
    """
    Rotate the x-tick labels if they are not numeric.
    """
    x_numeric, _ = are_axes_numeric(ax)
    if not x_numeric:
        for label in ax.get_xticklabels():
            label.set_rotation(45)
            label.set_horizontalalignment('right')
            label.set_rotation_mode('anchor')
            label.set_wrap(True)
        #ax.figure.tight_layout()  # Adjusts subplot parameters to give the plot more room


@dataclass(frozen=True)
class AxisParameters:
    title: str
    xlabel: str
    ylabel: str
    xscale: str
    yscale: str
    xlim: Tuple[float, float]
    ylim: Tuple[float, float]
    xticks: List[float]
    yticks: List[float]
    xticklabels: List[Union[str, float]]
    yticklabels: List[Union[str, float]]

    def is_x_axis_numeric(self) -> bool:
        """
        Check if all the ticks are numeric.
        """
        return all(isinstance(tick, (int, float)) for tick in self.xticks)

    def is_y_axis_numeric(self) -> bool:
        """
        Check if all the ticks are numeric.
        """
        return all(isinstance(tick, (int, float)) for tick in self.yticks)


def get_axis_parameters(ax: plt.Axes) -> AxisParameters:
    """
    Get the parameters of the axes.
    """
    return AxisParameters(
        title=ax.get_title(),
        xlabel=ax.get_xlabel(),
        ylabel=ax.get_ylabel(),
        xscale=ax.get_xscale(),
        yscale=ax.get_yscale(),
        xlim=ax.get_xlim(),
        ylim=ax.get_ylim(),
        xticks=ax.get_xticks(),
        yticks=ax.get_yticks(),
        xticklabels=ax.get_xticklabels(),
        yticklabels=ax.get_yticklabels(),
    )
