from dataclasses import dataclass, field
from typing import Iterable

from data_to_paper.utils.nice_list import NiceList

from .pvalue import TrackPValueCreationFuncs
from .random import SetRandomSeeds
from .scipy.override_scipy import ScipyPValueOverride
from .sklearn.override_sklearn import SklearnFitOverride, SklearnSearchLimitCheck, SklearnRandomStateOverride, \
    SklearnNNSizeOverride, SklearnPValue
from .statsmodels.override_statsmodels import StatsmodelsFitPValueOverride, StatsmodelsMultitestPValueOverride, \
    StatsmodelsAnovaPValueOverride, StatsmodelsMulticompPValueOverride
from ..base_run_contexts import RunContext, MultiRunContext
from ..run_issues import CodeProblem, RunIssue


@dataclass
class OverrideStatisticsPackages(MultiRunContext):
    """
    Base context manager for running GPT code.
    """
    issue_if_statistics_test_not_called: bool = True

    contexts: Iterable[RunContext] = field(default_factory=lambda: [
        ScipyPValueOverride(prevent_unpacking=True),
        SklearnFitOverride(),
        StatsmodelsFitPValueOverride(),
        StatsmodelsMultitestPValueOverride(),
        StatsmodelsAnovaPValueOverride(),
        StatsmodelsMulticompPValueOverride(),
        SklearnPValue(),
        SklearnSearchLimitCheck(),
        SklearnRandomStateOverride(),  # see comment below
        SklearnNNSizeOverride(),
        SetRandomSeeds(random_seed=0),
    ])
    # TODO: SklearnRandomStateOverride is kept for backwards compatability.
    #  It is likely not needed if we use SetRandomSeeds
    #  May undesirably lead to non-random results when iterating within the same run!

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.issue_if_statistics_test_not_called:
            stat_test_called = False
            stat_packages = set()
            for context in self.contexts:
                if isinstance(context, TrackPValueCreationFuncs):
                    stat_packages |= set(context.package_names)
                    if context.pvalue_creating_funcs:
                        stat_test_called = True
            if not stat_test_called:
                self.issues.append(RunIssue(
                    category='Statistics: good practice',
                    issue="We are writing code for an hypothesis-testing paper, "
                          "but your code does not call any statistical-testing function that returns a p-value.",
                    instructions="Please make sure that you perform a statistical-test with either "
                                 "{}.".format(sorted(NiceList(stat_packages, last_separator=', or '))),
                    code_problem=CodeProblem.NonBreakingRuntimeIssue,
                ))
        return super().__exit__(exc_type, exc_val, exc_tb)
