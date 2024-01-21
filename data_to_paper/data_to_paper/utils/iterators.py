from functools import partial

import pandas as pd

from itertools import zip_longest
from typing import Callable


def interleave(*iterators):
    """
    interleave([1, 2, 3], [4, 5, 6]) -> [1, 4, 2, 5, 3, 6]
    interleave([1, 2, 3], [4, 5], [7])) -> [1, 4, 7, 2, 5, 3]
    """
    sentinel = object()
    for tuple in zip_longest(*iterators, fillvalue=sentinel):
        for item in tuple:
            if item is not sentinel:
                yield item


def apply_deeply(obj, func: Callable, should_apply: Callable = None):
    """
    Apply a function to all elements of a nested object.
    """
    if isinstance(obj, dict):
        return {key: apply_deeply(value, func, should_apply) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple, set)):
        return type(obj)(apply_deeply(value, func, should_apply) for value in obj)
    elif isinstance(obj, pd.DataFrame):
        return obj.applymap(partial(apply_deeply, func=func, should_apply=should_apply))
    elif isinstance(obj, pd.Series):
        return obj.apply(partial(apply_deeply, func=func, should_apply=should_apply))
    elif should_apply is None or should_apply(obj):
        return func(obj)
    else:
        return obj
