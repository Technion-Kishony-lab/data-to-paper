import contextlib

from .scipy.override_scipy import scipy_label_pvalues
from .statsmodels.override_statsmodels import statsmodels_label_pvalues


@contextlib.contextmanager
def label_pvalues():
    with scipy_label_pvalues(), statsmodels_label_pvalues():
        yield
