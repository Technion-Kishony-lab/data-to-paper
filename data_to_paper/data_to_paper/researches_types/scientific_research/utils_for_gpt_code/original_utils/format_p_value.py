import numbers

import numpy as np

P_VALUE_MIN = 1e-6


def format_p_value(x):
    """
    Format a p-value to a string.
    """
    if not isinstance(x, numbers.Number):
        return x
    if x > 1 or x < 0:
        raise ValueError(f"p-value should be in the range [0, 1]. Got: {x}")
    # check if nan or inf
    if np.isinf(x) or np.isnan(x):
        return str(x)
    return "{:.3g}".format(x) if x >= P_VALUE_MIN else "<{}".format(P_VALUE_MIN)
