from dataclasses import dataclass
from typing import Iterable, Type

from .scipy.override_scipy import ScipyOverride
from .sklearn.override_sklearn import SklearnOverride, SklearnSearchLimitCheck, SklearnRandomStateOverride
from .statsmodels.override_statsmodels import StatsmodelsFitOverride, StatsmodelsMultitestOverride, \
    StatsmodelsAnovaOverride
from ..base_run_contexts import RunContext


@dataclass
class OverrideStatisticsPackages(RunContext):
    """
    Base context manager for running GPT code.
    """
    overrides: Iterable[Type[RunContext]] = (
        ScipyOverride, SklearnOverride, StatsmodelsFitOverride, StatsmodelsMultitestOverride, StatsmodelsAnovaOverride,
        SklearnSearchLimitCheck, SklearnRandomStateOverride)

    _contexts: Iterable[RunContext] = None

    def __enter__(self):
        self._contexts = [override() for override in self.overrides]
        for context in self._contexts:
            context.__enter__()
        return super().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        for context in self._contexts:
            context.__exit__(exc_type, exc_val, exc_tb)
        return super().__exit__(exc_type, exc_val, exc_tb)
