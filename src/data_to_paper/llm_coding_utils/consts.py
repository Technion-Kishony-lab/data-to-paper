# ALLOWED_PLOT_KINDS = ['line', 'scatter', 'bar', 'hist', 'box', 'kde', 'hexbin', 'pie']
import numbers
from typing import Union

from data_to_paper.utils.mutable import Mutable


AXES_SIZE_INCHES = (2.6, 2)  # actual size of the axes box in inches (not including labels, etc.)
FIG_SIZE_INCHES = (4, 3)  # this is not consequential, as we fit the figure to the axes (using fit_fig_to_axes)

FIG_DPI = Mutable(400)

ALLOWED_PLOT_KINDS = ['bar']  # TODO: Add support for more plot kinds

DF_ALLOWED_VALUE_TYPES = (numbers.Number, str, bool, tuple)
DF_ALLOWED_COLUMN_TYPES = (numbers.Number, str, bool)
DfColumnTyping = Union[numbers.Number, str, bool]  # not tuple because we need tuple to choose a pair of columns
