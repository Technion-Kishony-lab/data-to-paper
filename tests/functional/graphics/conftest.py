import numpy as np
import pandas as pd
import pytest


@pytest.fixture()
def test_data():
    x = range(10)
    np.random.seed(0)
    y = np.random.randn(10)
    y_2 = np.random.randn(10)
    y_err = np.random.rand(10) * 0.1
    y_ci_lower = y - np.random.rand(10) * 0.5
    y_ci_upper = y + np.random.rand(10) * 0.5
    y_p_value = np.random.rand(10) * 0.05
    df = pd.DataFrame({
        'x': x,
        'y': y,
        'y_2': y_2,
        'y_err': y_err,
        'y_ci_lower': y_ci_lower,
        'y_ci_upper': y_ci_upper,
        'y_ci': list(zip(y_ci_lower, y_ci_upper)),
        'y_p_value': y_p_value,
    })
    yield df


@pytest.fixture()
def df_for_plot():
    data = {
        'apples': [3, 2, 5, 7, 2],
        'oranges': [1, 5, 3, 8, 6],
        'bananas': [3, 4, 2, 1, 5],
        'apples_err': [0.5, 4.3, 0.6, 0.2, 0.4],
        'oranges_err': [(0.3, 0.5), (0.4, 0.6), (0.5, 0.2), (0.1, 0.3), (0.3, 0.4)],
        'bananas_err': [0.2, 0.3, 0.1, 0.5, 0.4],
        'apples_ci': [(2.5, 3.5), (1.7, 2.3), (4.4, 5.6), (6.8, 7.2), (1.6, 2.4)],
        'oranges_ci': [(0.8, 1.2), (4.4, 5.6), (2.8, 3.2), (7.7, 8.3), (5.6, 6.4)],
        'bananas_ci': [(2.8, 3.2), (3.8, 4.2), (1.8, 2.2), (0.7, 1.3), (4.6, 5.4)],
        'apples_p_value': [0.1, 0.002, 0.3, 0.4, 0.5],
        'oranges_p_value': [0.1, 0.2, 0.001, 0.4, 0.5],
        'bananas_p_value': [0.1, 0.2, 0.3, 0.00001, 0.5]
    }
    df = pd.DataFrame(data)
    return df
