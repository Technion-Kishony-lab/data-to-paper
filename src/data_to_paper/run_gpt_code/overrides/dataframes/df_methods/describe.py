# pragma: no cover
"""
Obsolete. We are now enforcing removal of min/max in rule-based review.
"""

from typing import Optional
from pandas.core.frame import DataFrame


class ModifiedDescribeDF(DataFrame):
    def _drop_rows(self, drop_count: Optional[bool] = False):
        to_drop = ['min', '25%', '50%', '75%', 'max']
        if drop_count or drop_count is None and all(self.loc['count'] == self.loc['count'][0]):
            # if all counts are the same, we drop the count row
            to_drop.append('count')
        return self.drop(to_drop)

    def __str__(self):
        return DataFrame.__str__(self._drop_rows())

    def __repr__(self):
        return DataFrame.__repr__(self._drop_rows())

    def to_string(self, *args, **kwargs):
        return DataFrame.to_string(self._drop_rows(), *args, **kwargs)

    # def to_latex(self, *args, **kwargs):
    #     return DataFrame.to_latex(self._drop_rows(drop_count=None), *args, **kwargs)


def describe(self, *args, original_method=None, on_change=None, **kwargs):
    """
    Removes the min, 25%, 50%, 75%, max rows from the result of the original describe function.
    """
    result = original_method(self, *args, **kwargs)
    return ModifiedDescribeDF(result)
