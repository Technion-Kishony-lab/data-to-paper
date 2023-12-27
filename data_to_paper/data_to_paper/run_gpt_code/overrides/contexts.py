from dataclasses import dataclass, field
from typing import Iterable

from .pvalue import TrackPValueCreationFuncs
from .scipy.override_scipy import ScipyPValueOverride
from .sklearn.override_sklearn import SklearnFitOverride, SklearnSearchLimitCheck, SklearnRandomStateOverride, \
    SklearnNNSizeOverride
from .statsmodels.override_statsmodels import StatsmodelsFitPValueOverride, StatsmodelsMultitestPValueOverride, \
    StatsmodelsAnovaPValueOverride
from ..base_run_contexts import RunContext, MultiRunContext
from ..types import RunIssue, CodeProblem


@dataclass
class OverrideStatisticsPackages(MultiRunContext):
    """
    Base context manager for running GPT code.
    """
    issue_if_statistics_test_not_called: bool = True

    contexts: Iterable[RunContext] = field(default_factory=lambda: [
        ScipyPValueOverride(),
        SklearnFitOverride(),
        StatsmodelsFitPValueOverride(),
        StatsmodelsMultitestPValueOverride(),
        StatsmodelsAnovaPValueOverride(),
        SklearnSearchLimitCheck(),
        SklearnRandomStateOverride(),
        SklearnNNSizeOverride(),
    ])

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.issue_if_statistics_test_not_called:
            stat_test_called = False
            for context in self.contexts:
                if isinstance(context, TrackPValueCreationFuncs):
                    if context.pvalue_creating_funcs:
                        stat_test_called = True
                        break
            if not stat_test_called:
                self.issues.append(RunIssue(
                    issue="The code does not call any statistical-testing function that creates a p-value.",
                    instructions="We are writing code for an hypothesis-testing paper. "
                                 "Please make sure that you call a statistical-testing function that creates a p-value.",
                    code_problem=CodeProblem.NonBreakingRuntimeIssue,
                ))
        return super().__exit__(exc_type, exc_val, exc_tb)
