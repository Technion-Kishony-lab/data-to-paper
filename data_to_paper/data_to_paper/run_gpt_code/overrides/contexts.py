import contextlib

from .scipy.override_scipy import scipy_override
from .sklearn.override_sklearn import sklearn_override
from .statsmodels.override_statsmodels import statsmodels_override


@contextlib.contextmanager
def override_statistics_packages():
    with \
            scipy_override(), \
            sklearn_override(), \
            statsmodels_override():
        yield
