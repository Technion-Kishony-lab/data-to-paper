from dataclasses import dataclass
from typing import Dict, Any, List, Set

import pytest
import sys

from scientistgpt.base_steps import PythonValueReviewBackgroundProductsConverser, \
    PythonDictWithDefinedKeysReviewBackgroundProductsConverser
from scientistgpt.servers.chatgpt import OPENAI_SERVER_CALLER
from scientistgpt.utils.types import ListBasedSet

from .utils import TestProductsReviewGPT, check_wrong_and_right_responses

PYTHON_VERSION_MINOR = sys.version_info[1]


@dataclass
class TestPythonValueReviewBackgroundProductsConverser(TestProductsReviewGPT,
                                                       PythonValueReviewBackgroundProductsConverser):
    pass


@dataclass
class TestPythonDictWithDefinedKeysProductsReviewGPT(TestProductsReviewGPT,
                                                     PythonDictWithDefinedKeysReviewBackgroundProductsConverser):
    pass


correct_dict_str_any_value = r"""{'a': '1', 'b': {'2' : '2'}, 'c': [3, 3, 3]}"""

correct_dict_str_str_value = r"""{'a': '1', 'b': '2', 'c': '3'}"""
error_message_include_dict_str_str_value = "Your response should be formatted as"

correct_list_str_value = r"""['a', 'b', 'c']"""


@pytest.mark.parametrize('correct_python_value, value_type', [
    (correct_dict_str_any_value, Dict[str, Any]),
    (correct_dict_str_str_value, Dict[str, str]),
    (correct_list_str_value, List[str]),
])
def test_request_python_value(correct_python_value, value_type):
    check_wrong_and_right_responses(
        responses=[f'Here is the correct python value:\n{correct_python_value}\nShould be all good.'],
        requester=TestPythonValueReviewBackgroundProductsConverser(value_type=value_type),
        correct_value=eval(correct_python_value))


@pytest.mark.parametrize('non_correct_python_value, correct_python_value, value_type, error_should_include', [
    (correct_dict_str_any_value.replace('}', ''), correct_dict_str_any_value, Dict[str, Any],
     "flanked by `{` and `}`"),
    (correct_dict_str_str_value.replace("'3'", "3"), correct_dict_str_str_value, Dict[str, str],
     "The dict values must be of type: <class 'str'>"),
    (correct_dict_str_str_value.replace("'a'", "3"), correct_dict_str_str_value, Dict[str, str],
     "The dict keys must be of type: <class 'str'>"),
    (correct_dict_str_str_value, "{'a', 'b'}", Set[str],
     "object is not of type:"),
    (correct_list_str_value.replace("'c'", "5"), correct_list_str_value, List[str],
     "The values must be of type: <class 'str'>"),
    (correct_list_str_value.replace("'c'", "'c"), correct_list_str_value, List[str],
     "EOL while scanning string literal" if PYTHON_VERSION_MINOR <= 9 else "unterminated string literal"),
])
def test_request_python_value_with_error(
        non_correct_python_value, correct_python_value, value_type, error_should_include):
    check_wrong_and_right_responses(
        responses=[f'Here is some wrong python value:\n{non_correct_python_value}\nCheck it out.',
                   f'Here is the correct python value:\n{correct_python_value}\nShould be fine now.'],
        requester=TestPythonValueReviewBackgroundProductsConverser(value_type=value_type,
                                                                   rewind_after_end_of_review=None,
                                                                   rewind_after_getting_a_valid_response=None),
        correct_value=eval(correct_python_value),
        error_texts=error_should_include)


@pytest.mark.parametrize('non_correct_python_value, correct_python_value, value_type, error_should_include', [
    (correct_dict_str_any_value.replace("'a'", "'aa'"), correct_dict_str_any_value, Dict[str, Any],
     "the keys: {'a', 'b', 'c'}"),
])
def test_request_python_defined_keys_dict_with_error(
        non_correct_python_value, correct_python_value, value_type, error_should_include):
    check_wrong_and_right_responses(
        [f'Here is some wrong python value:\n{non_correct_python_value}\nCheck it out.',
         f'Here is the correct python value:\n{correct_python_value}\nShould be fine now.'],
        requester=TestPythonDictWithDefinedKeysProductsReviewGPT(value_type=value_type,
                                                                 requested_keys=ListBasedSet(['a', 'b', 'c']),
                                                                 rewind_after_end_of_review=None,
                                                                 rewind_after_getting_a_valid_response=None),
        correct_value=eval(correct_python_value),
        error_texts=error_should_include)


def test_request_python_ends_with_reposting_fresh_response():
    requester = TestPythonValueReviewBackgroundProductsConverser(value_type=List[str])
    with OPENAI_SERVER_CALLER.mock([
            f'Here is the list:\n{correct_list_str_value}\n'],
            record_more_if_needed=False):
        assert requester.run_dialog_and_get_valid_result() == eval(correct_list_str_value)
    assert len(requester.conversation) == 3

    # Response is reposted as fresh:
    assert requester.conversation[-1].content == correct_list_str_value
