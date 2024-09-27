import pickle

import pandas
from pytest import raises

from data_to_paper.run_gpt_code.overrides.dataframes.df_methods.methods import DataframeKeyError
from data_to_paper.run_gpt_code.attr_replacers import PreventAssignmentToAttrs, AttrReplacer
from tests.functional.run_gpt_code.fake_cls import TestDoNotAssign


def test_prevent_assignment_to_attr():
    t = TestDoNotAssign()
    with PreventAssignmentToAttrs(obj_import_str=TestDoNotAssign,
                                  forbidden_set_attrs=['not_allowed']):
        t.allowed = 1
        with raises(AttributeError) as exc:
            t.not_allowed = 1

    assert 'not_allowed' in str(exc.value)
    assert t.allowed == 1
    assert t.not_allowed == 0


def test_prevent_assignment_to_attr_is_permissive_internally():
    t = TestDoNotAssign()
    with PreventAssignmentToAttrs(obj_import_str=TestDoNotAssign,
                                  forbidden_set_attrs=['not_allowed']):
        with raises(AttributeError):
            t.not_allowed = 1
        t.set_internally(7)

    assert t.not_allowed == 7


def _wrapper(*args, **kwargs):
    return 7


def test_attr_replacer():
    attr_replacer = AttrReplacer(attr='DataFrame', obj_import_str='pandas', wrapper=_wrapper)
    with attr_replacer:
        assert pandas.DataFrame({'a': [1]}) == 7
    assert pandas.DataFrame({'a': [1]})['a'][0] == 1


def test_attr_replacer_is_serializable():
    attr_replacer = AttrReplacer(attr='DataFrame', obj_import_str='pandas', wrapper=_wrapper)
    pickle.dumps(attr_replacer)


def test_dataframe_key_error_is_serializable():
    error = DataframeKeyError(original_error=KeyError("Test error"), key="test_key",
                              available_keys=["key1", "key2"])

    pickled_error = pickle.dumps(error)
    unpickled_error = pickle.loads(pickled_error)

    assert error.original_error.args == unpickled_error.original_error.args, \
        "Original error arguments do not match unpickled error arguments"
    assert error.key == unpickled_error.key, "Original error key does not match unpickled error key"
    assert error.available_keys == unpickled_error.available_keys, \
        "Original error available keys do not match unpickled error available keys"
