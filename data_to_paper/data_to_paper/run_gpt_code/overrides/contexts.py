import contextlib

from .scipy.override_scipy import ScipyOverride
from .sklearn.override_sklearn import SklearnOverride
from .statsmodels.override_statsmodels import StatsmodelsOverride


@contextlib.contextmanager
def override_statistics_packages():
    with \
            ScipyOverride(), \
            SklearnOverride(), \
            StatsmodelsOverride():
        yield
