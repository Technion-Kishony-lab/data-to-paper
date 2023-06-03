from dataclasses import dataclass
from typing import Dict, Any, List

import pytest

from scientistgpt.base_steps import BasePythonValueProductsReviewGPT, PythonDictWithDefinedKeysProductsReviewGPT
from scientistgpt.utils.types import ListBasedSet

from .utils import TestProductsReviewGPT, check_wrong_and_right_responses


@dataclass
class TestBasePythonValueProductsReviewGPT(TestProductsReviewGPT, BasePythonValueProductsReviewGPT):
    pass


@dataclass
class TestPythonDictWithDefinedKeysProductsReviewGPT(TestProductsReviewGPT, PythonDictWithDefinedKeysProductsReviewGPT):
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
        requester=TestBasePythonValueProductsReviewGPT(value_type=value_type),
        correct_value=eval(correct_python_value))


@pytest.mark.parametrize('non_correct_python_value, correct_python_value, value_type, error_should_include', [
    (correct_dict_str_any_value.replace('}', ''), correct_dict_str_any_value, Dict[str, Any],
     "flanked by `{` and `}`"),
    (correct_dict_str_str_value.replace("'3'", "3"), correct_dict_str_str_value, Dict[str, str],
     "The dict values must be of type: <class 'str'>"),
    (correct_dict_str_str_value.replace("'a'", "3"), correct_dict_str_str_value, Dict[str, str],
     "The dict keys must be of type: <class 'str'>"),
    (correct_list_str_value.replace("'c'", "5"), correct_list_str_value, List[str],
     "The values must be of type: <class 'str'>"),
    (correct_list_str_value.replace("'c'", "'c"), correct_list_str_value, List[str],
     "EOL while scanning string literal"),
])
def test_request_python_value_with_error(
        non_correct_python_value, correct_python_value, value_type, error_should_include):
    check_wrong_and_right_responses(
        responses=[f'Here is some wrong python value:\n{non_correct_python_value}\nCheck it out.',
                   f'Here is the correct python value:\n{correct_python_value}\nShould be fine now.'],
        requester=TestBasePythonValueProductsReviewGPT(value_type=value_type),
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
                                                                 requested_keys=ListBasedSet(['a', 'b', 'c'])),
        correct_value=eval(correct_python_value),
        error_texts=error_should_include)
