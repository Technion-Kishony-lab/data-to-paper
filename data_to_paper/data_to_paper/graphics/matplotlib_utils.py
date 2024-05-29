from typing import Tuple, Optional

from matplotlib import pyplot as plt


def get_xy_coordinates_of_df_plot(df, x=None, y=None, kind='line'):
    """
    Plots the DataFrame and retrieves x and y coordinates for each data point using numerical indices.
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
    legend = ax.legend()
    legend_keys = [text.get_text() for text in legend.get_texts()]
    is_singleton = len(legend_keys) == 1
    if not is_singleton:
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
    return singleton_legend_key


def add_grid_line_at_zero_if_not_origin(ax: plt.Axes, h_or_v: str):
    """
    Add a grid line at zero, if zero is within the axis limits.
    h_or_v: 'h' for horizontal, 'v' for vertical, 'hv' for both.
    """
    if 'h' in h_or_v:
        if ax.ylim[0] < 0 < ax.ylim[1]:
            ax.axhline(0, color='grey', linewidth=0.8, linestyle='--')
    if 'v' in h_or_v:
        if ax.xlim[0] < 0 < ax.xlim[1]:
            ax.axvline(0, color='grey', linewidth=0.8, linestyle='--')


def rotate_xticklabels_if_not_numeric(ax: plt.Axes):
    """
    Rotate the x-tick labels if they are not numeric.
    """
    x_numeric, _ = are_axes_numeric(ax)
    if not x_numeric:
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right",
                           rotation_mode="anchor", wrap=True)
        ax.tight_layout()  # Adjusts subplot parameters to give the plot more room


def raise_if_numeric_axes_do_not_have_labels(ax: plt.Axes):
    """
    Raise an error if the axes are numeric and do not have labels.
    """
    x_numeric, y_numeric = are_axes_numeric(ax)
    msgs = []
    if x_numeric and not ax.get_xlabel():
        msgs.append('The x-axis is numeric, but it does not have a label. Use `xlabel=` to add a label.')
    if y_numeric and not ax.get_ylabel():
        msgs.append('The y-axis is numeric, but it does not have a label. Use `ylabel=` to add a label.')
    if msgs:
        msg = 'All axes with numeric labels must have labels.\n' + '\n'.join(msgs)
        raise ValueError(msg)
