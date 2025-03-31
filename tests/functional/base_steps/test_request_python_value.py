from dataclasses import dataclass
from typing import Dict, Any, List, Set

import pytest
import sys

from data_to_paper.base_steps import (
    PythonValueReviewBackgroundProductsConverser,
    PythonDictWithDefinedKeysReviewBackgroundProductsConverser,
)
from data_to_paper.base_steps.result_converser import Rewind
from data_to_paper.servers.llm_call import LLM_SERVER_CALLER
from data_to_paper.servers.model_engine import ModelEngine
from data_to_paper.servers.model_manager import ModelManager
from data_to_paper.utils.types import ListBasedSet

from .utils import (
    TestProductsReviewGPT,
    check_wrong_and_right_responses,
    replace_apply_get_and_append_assistant_message,
)

PYTHON_VERSION_MINOR = sys.version_info[1]


@dataclass
class TestPythonValueReviewBackgroundProductsConverser(
    TestProductsReviewGPT, PythonValueReviewBackgroundProductsConverser
):
    pass


@dataclass
class TestPythonDictWithDefinedKeysProductsReviewGPT(
    TestProductsReviewGPT, PythonDictWithDefinedKeysReviewBackgroundProductsConverser
):
    pass


correct_dict_str_any_value = r"""{'a': '1', 'b': {'2' : '2'}, 'c': [3, 3, 3]}"""

correct_dict_str_str_value = r"""{'a': '1', 'b': '2', 'c': '3'}"""
error_message_include_dict_str_str_value = "Your response should be formatted as"

correct_list_str_value = r"""['a', 'b', 'c']"""


def test_request_python_value_json_mode():
    with LLM_SERVER_CALLER.mock(
        ['\n{\n    "primes": [2, 3, 5, 7, 11, 13, 17, 19]\n}\n'],
        record_more_if_needed=False,
    ):
        converser = TestPythonValueReviewBackgroundProductsConverser(
            value_type=Dict[str, Any],
            json_mode=True,
            model_engine=ModelEngine(ModelManager.get_instance().get_current_model()),
            mission_prompt="Please return a list of all prime numbers from 1 to 20. "
            "Return your response as json value.",
        )
        result = converser.run_and_get_valid_result()
    assert result == {"primes": [2, 3, 5, 7, 11, 13, 17, 19]}


@pytest.mark.parametrize(
    "correct_python_value, value_type",
    [
        (correct_dict_str_any_value, Dict[str, Any]),
        (correct_dict_str_str_value, Dict[str, str]),
        (correct_list_str_value, List[str]),
    ],
)
def test_request_python_value(correct_python_value, value_type):
    check_wrong_and_right_responses(
        responses=[
            f"Here is the correct python value:\n{correct_python_value}\nShould be all good."
        ],
        requester=TestPythonValueReviewBackgroundProductsConverser(
            value_type=value_type
        ),
        correct_value=eval(correct_python_value),
    )


@pytest.mark.parametrize(
    "non_correct_python_value, correct_python_value, value_type, error_should_include",
    [
        (
            correct_dict_str_any_value.replace("}", ""),
            correct_dict_str_any_value,
            Dict[str, Any],
            "wrapped within a triple backtick",
        ),
        (
            correct_dict_str_str_value.replace("'3'", "3"),
            correct_dict_str_str_value,
            Dict[str, str],
            "object within the dict values must be of type `str`",
        ),
        (
            correct_dict_str_str_value.replace("'a'", "3"),
            correct_dict_str_str_value,
            Dict[str, str],
            "object within the dict keys must be of type `str`",
        ),
        (
            correct_dict_str_str_value,
            "{'a', 'b'}",
            Set[str],
            "object must be of type `set`",
        ),
        (
            correct_list_str_value.replace("'c'", "5"),
            correct_list_str_value,
            List[str],
            "object within the list must be of type `str`",
        ),
        (
            correct_list_str_value.replace("'c'", "'c"),
            correct_list_str_value,
            List[str],
            "EOL while scanning string literal"
            if PYTHON_VERSION_MINOR <= 9
            else "unterminated string literal",
        ),
    ],
)
def test_request_python_value_with_error(
    non_correct_python_value, correct_python_value, value_type, error_should_include
):
    check_wrong_and_right_responses(
        responses=[
            f"Here is some wrong python value:\n{non_correct_python_value}\nCheck it out.",
            f"Here is the correct python value:\n{correct_python_value}\nShould be fine now.",
        ],
        requester=TestPythonValueReviewBackgroundProductsConverser(
            value_type=value_type,
            rewind_after_end_of_review=None,
            rewind_after_getting_a_valid_response=None,
        ),
        correct_value=eval(correct_python_value),
        error_texts=error_should_include,
    )


@pytest.mark.parametrize(
    "default_rewind, answers_contexts",
    [
        (
            Rewind.AS_FRESH,
            [
                (correct_list_str_value.replace("]", ""), []),
                (
                    correct_list_str_value.replace("]", ""),
                    ["#0", "a valid Python"],
                ),  # 'a valid Python' -> format error
                (
                    correct_list_str_value.replace("'c'", "5"),
                    ["#0", "a valid Python"],
                ),  # 'a valid Python' -> format error
                (
                    correct_list_str_value,
                    ["Python", "`str`"],
                ),  # 'python' -> reposted as fresh; `str` -> content error
            ],
        ),
        (
            Rewind.AS_FRESH_CORRECTION,
            [
                (correct_list_str_value.replace("]", ""), []),
                (correct_list_str_value.replace("]", ""), ["#0", "a valid Python"]),
                (correct_list_str_value.replace("'c'", "5"), ["#0", "a valid Python"]),
                (correct_list_str_value, ["#0", "a valid Python", "Python", "`str`"]),
            ],
        ),
    ],
)
def test_request_python_error_messages(default_rewind, answers_contexts):
    responses = [
        f"#{i} is {answer_and_context[0]}"
        for i, answer_and_context in enumerate(answers_contexts)
    ]
    contexts = [answer_and_context[1] for answer_and_context in answers_contexts]
    requester = TestPythonValueReviewBackgroundProductsConverser(
        value_type=List[str], default_rewind_for_result_error=default_rewind
    )
    replace_apply_get_and_append_assistant_message(requester)
    with LLM_SERVER_CALLER.mock(responses, record_more_if_needed=False):
        assert requester.run_and_get_valid_result() == eval(correct_list_str_value)
    for i, context in enumerate(contexts):
        called_with_context = requester.called_with_contexts[i][
            2:
        ]  # remove SYSTEM and USER PROMPT
        assert len(called_with_context) == len(context)
        for message, context_part in zip(called_with_context, context):
            assert context_part in message.content


@pytest.mark.parametrize(
    "non_correct_python_value, correct_python_value, value_type, error_should_include",
    [
        (
            correct_dict_str_any_value.replace("'a'", "'aa'"),
            correct_dict_str_any_value,
            Dict[str, Any],
            "the keys: {'a', 'b', 'c'}",
        ),
    ],
)
def test_request_python_defined_keys_dict_with_error(
    non_correct_python_value, correct_python_value, value_type, error_should_include
):
    check_wrong_and_right_responses(
        [
            f"Here is some wrong python value:\n{non_correct_python_value}\nCheck it out.",
            f"Here is the correct python value:\n{correct_python_value}\nShould be fine now.",
        ],
        requester=TestPythonDictWithDefinedKeysProductsReviewGPT(
            value_type=value_type,
            requested_keys=ListBasedSet(["a", "b", "c"]),
            rewind_after_end_of_review=None,
            rewind_after_getting_a_valid_response=None,
        ),
        correct_value=eval(correct_python_value),
        error_texts=error_should_include,
    )


def test_request_python_ends_with_reposting_fresh_response():
    requester = TestPythonValueReviewBackgroundProductsConverser(value_type=List[str])
    with LLM_SERVER_CALLER.mock(
        [f"Here is the list:\n{correct_list_str_value}\n"], record_more_if_needed=False
    ):
        assert requester.run_and_get_valid_result() == eval(correct_list_str_value)
    assert len(requester.conversation) == 3

    # Response is reposted as fresh:
    assert (
        requester.conversation[-1].content
        == f"```Python\n{correct_list_str_value}\n```"
    )
