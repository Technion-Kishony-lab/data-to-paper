import pickle

from _pytest.fixtures import fixture
from pandas.core.dtypes.inference import is_list_like
from pandas import DataFrame

from data_to_paper.run_gpt_code.overrides.pvalue import PValue, is_p_value


@fixture()
def pvalue():
    return PValue(0.1)


def test_pvalue_type(pvalue):
    assert is_p_value(pvalue)
    assert isinstance(pvalue, PValue)
    assert pvalue.value == 0.1
    assert pvalue.created_by is None


def test_pvalue_is_list_like(pvalue):
    assert is_list_like(pvalue) is False


def test_pvalue_pickleability(pvalue):
    # Pickle the PValue object
    pickled_pvalue = pickle.dumps(pvalue)

    # Unpickle the PValue object
    unpickled_pvalue = pickle.loads(pickled_pvalue)

    # Assert that the unpickled object is still a PValue and retains its properties
    assert isinstance(unpickled_pvalue, PValue)
    assert unpickled_pvalue.value == pvalue.value
    assert unpickled_pvalue.created_by == pvalue.created_by


def test_pvalue_unique():
    df = DataFrame({'a': [PValue(2), PValue(1), PValue(2)]})
    data = df.iloc[:, 0]
    data_unique = data.unique()
    assert len(data_unique) == 2
    assert isinstance(data_unique[0], PValue)
