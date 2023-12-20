from dataclasses import dataclass
from typing import Iterable

from .scipy.override_scipy import ScipyPValueOverride
from .sklearn.override_sklearn import SklearnFitOverride, SklearnSearchLimitCheck, SklearnRandomStateOverride, \
    SklearnNNSizeOverride
from .statsmodels.override_statsmodels import StatsmodelsFitPValueOverride, StatsmodelsMultitestPValueOverride, \
    StatsmodelsAnovaPValueOverride
from ..base_run_contexts import RunContext


@dataclass
class OverrideStatisticsPackages(RunContext):
    """
    Base context manager for running GPT code.
    """
    overrides: Iterable[RunContext] = (
        ScipyPValueOverride(),
        SklearnFitOverride(),
        StatsmodelsFitPValueOverride(),
        StatsmodelsMultitestPValueOverride(),
        StatsmodelsAnovaPValueOverride(),
        SklearnSearchLimitCheck(),
        SklearnRandomStateOverride(),
        SklearnNNSizeOverride(),
    )

    def __enter__(self):
        for context in self.overrides:
            context.__enter__()
        return super().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        for context in self.overrides:
            context.__exit__(exc_type, exc_val, exc_tb)
        return super().__exit__(exc_type, exc_val, exc_tb)
