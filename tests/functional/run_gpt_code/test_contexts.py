import os
from dataclasses import dataclass

from _pytest.python_api import raises

from data_to_paper.run_gpt_code.overrides.attr_replacers import PreventAssignmentToAttrs
from tests.functional.run_gpt_code.conftest import TestDoNotAssign

# get the name of this file without the path:
THIS_FILE = os.path.basename(__file__)


def test_prevent_assignment_to_attr():
    t = TestDoNotAssign()
    with PreventAssignmentToAttrs(cls=TestDoNotAssign, forbidden_set_attrs=['not_allowed'], module_filename=THIS_FILE):
        t.allowed = 1
        with raises(AttributeError) as exc:
            t.not_allowed = 1

    assert 'not_allowed' in str(exc.value)
    assert t.allowed == 1
    assert t.not_allowed == 0


def test_prevent_assignment_to_attr_is_permissive_internally():
    t = TestDoNotAssign()
    with PreventAssignmentToAttrs(cls=TestDoNotAssign, forbidden_set_attrs=['not_allowed'], module_filename=THIS_FILE):
        with raises(AttributeError):
            t.not_allowed = 1
        t.set_internally(7)

    assert t.not_allowed == 7
