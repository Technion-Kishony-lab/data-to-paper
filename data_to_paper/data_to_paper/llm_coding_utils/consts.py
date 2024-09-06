# ALLOWED_PLOT_KINDS = ['line', 'scatter', 'bar', 'hist', 'box', 'kde', 'hexbin', 'pie']
import numbers
from typing import Union

FIG_SIZE_INCHES = (4, 3)

ALLOWED_PLOT_KINDS = ['bar']  # TODO: Add support for more plot kinds

DF_ALLOWED_TYPES = (numbers.Number, str, bool, tuple)
DfAllowedTyping = Union[numbers.Number, str, bool, tuple]
