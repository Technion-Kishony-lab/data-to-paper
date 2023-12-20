from dataclasses import dataclass
from typing import Iterable

from .scipy.override_scipy import ScipyPValueOverride
from .sklearn.override_sklearn import SklearnFitOverride, SklearnSearchLimitCheck, SklearnRandomStateOverride, \
    SklearnNNSizeOverride
from .statsmodels.override_statsmodels import StatsmodelsFitPValueOverride, StatsmodelsMultitestPValueOverride, \
    StatsmodelsAnovaPValueOverride
from ..base_run_contexts import RunContext, MultiRunContext


@dataclass
class OverrideStatisticsPackages(MultiRunContext):
    """
    Base context manager for running GPT code.
    """
    contexts: Iterable[RunContext] = (
        ScipyPValueOverride(),
        SklearnFitOverride(),
        StatsmodelsFitPValueOverride(),
        StatsmodelsMultitestPValueOverride(),
        StatsmodelsAnovaPValueOverride(),
        SklearnSearchLimitCheck(),
        SklearnRandomStateOverride(),
        SklearnNNSizeOverride(),
    )
