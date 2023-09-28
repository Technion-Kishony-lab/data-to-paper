from _pytest.fixtures import fixture
from pandas.core.dtypes.inference import is_list_like

from data_to_paper.run_gpt_code.overrides.types import PValue, is_p_value


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
