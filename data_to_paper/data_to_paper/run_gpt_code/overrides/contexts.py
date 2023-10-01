import contextlib

from .scipy.override_scipy import ScipyOverride
from .sklearn.override_sklearn import SklearnOverride
from .statsmodels.override_statsmodels import StatsmodelsFitOverride, StatsmodelsMultitestOverride, \
    StatsmodelsAnovaOverride


@contextlib.contextmanager
def override_statistics_packages():
    with \
            ScipyOverride(), \
            SklearnOverride(), \
            StatsmodelsFitOverride(), \
            StatsmodelsMultitestOverride(), \
            StatsmodelsAnovaOverride():
        yield
