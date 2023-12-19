import os
import time
import pickle

import pandas
from _pytest.python_api import raises

from data_to_paper.run_gpt_code.timeout_context import timeout_context
from data_to_paper.run_gpt_code.overrides.attr_replacers import PreventAssignmentToAttrs, AttrReplacer
from tests.functional.run_gpt_code.conftest import TestDoNotAssign

# get the name of this file without the path:
THIS_FILE = os.path.basename(__file__)


def test_prevent_assignment_to_attr():
    t = TestDoNotAssign()
    with PreventAssignmentToAttrs(obj_import_str=TestDoNotAssign, forbidden_set_attrs=['not_allowed'], module_filename=THIS_FILE):
        t.allowed = 1
        with raises(AttributeError) as exc:
            t.not_allowed = 1

    assert 'not_allowed' in str(exc.value)
    assert t.allowed == 1
    assert t.not_allowed == 0


def test_prevent_assignment_to_attr_is_permissive_internally():
    t = TestDoNotAssign()
    with PreventAssignmentToAttrs(obj_import_str=TestDoNotAssign, forbidden_set_attrs=['not_allowed'], module_filename=THIS_FILE):
        with raises(AttributeError):
            t.not_allowed = 1
        t.set_internally(7)

    assert t.not_allowed == 7


def test_timeout_context():
    with timeout_context(1):
        pass
    with raises(TimeoutError):
        with timeout_context(1):
            time.sleep(2)


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
