from __future__ import annotations
from typing import TYPE_CHECKING

from data_to_paper.utils.mutable import Mutable
ON_CHANGE = Mutable(None)

if TYPE_CHECKING:
    from .dataframe_operations import DataframeOperation


def notify_on_change(self, operation: DataframeOperation):
    if ON_CHANGE.val is not None:
        ON_CHANGE.val(self, operation)
