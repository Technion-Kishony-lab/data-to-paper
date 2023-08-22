import pandas as pd
from _pytest.fixtures import fixture

from data_to_paper.utils.dataframe import extract_df_axes_labels


@fixture
def df():
    columns = pd.MultiIndex.from_tuples([
        ('A', 'cat', 'white'), ('A', 'dog', 'black'),
        ('B', 'cat', 'black'), ('B', 'dog', 'white')
    ], names=['letters', 'animals', 'colors'])

    index = pd.MultiIndex.from_tuples([
        (1, 'X', 'alpha'), (1, 'Y', 'beta'),
        (2, 'X', 'gamma'), (2, 'Y', 'delta')
    ], names=['numbers', 'alphabets', 'greek'])

    data = [[7, 5, 9, 2], [0, 4, 2, 0], [8, 6, 8, 7], [5, 1, 7, 9]]
    return pd.DataFrame(data, columns=columns, index=index)



def test_extract_headers():
    df = pd.DataFrame([[1, 2], [3, 4]], columns=['A', 'B'], index=['X', 'Y'])
    assert extract_df_axes_labels(df) == {'A', 'B', 'X', 'Y'}


def test_extract_headers_from_multi_index(df):
    assert extract_df_axes_labels(df) == \
           {'A', 'B', 'cat', 'dog', 'white', 'black', 1, 2, 'X', 'Y', 'alpha', 'beta', 'gamma', 'delta'}
