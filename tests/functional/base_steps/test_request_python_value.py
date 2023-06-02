from dataclasses import dataclass, field
from typing import Dict, Any, List

import pytest

from scientistgpt.base_steps import BasePythonValueProductsReviewGPT
from scientistgpt.conversation.actions_and_conversations import ActionsAndConversations
from scientistgpt.servers.chatgpt import OPENAI_SERVER_CALLER

from .utils import TestAgent


@dataclass
class TestBasePythonValueProductsReviewGPT(BasePythonValueProductsReviewGPT):
    conversation_name: str = 'test'
    user_agent: TestAgent = TestAgent.PERFORMER
    assistant_agent: TestAgent = TestAgent.REVIEWER
    actions_and_conversations: ActionsAndConversations = field(default_factory=ActionsAndConversations)
    max_reviewing_rounds: int = 0


correct_dict_str_any_value = r"""{'a': '1', 'b': {'2' : '2'}, 'c': [3, 3, 3]}"""

correct_dict_str_str_value = r"""{'a': '1', 'b': '2', 'c': '3'}"""
error_message_include_dict_str_str_value = "Your response should be formatted as"

correct_list_str_value = r"""['a', 'b', 'c']"""
non_correct_list_str_value = r"""['a', 'b', 5]"""


@pytest.mark.parametrize('correct_python_value, value_type', [
    (correct_dict_str_any_value, Dict[str, Any]),
    (correct_dict_str_str_value, Dict[str, str]),
    (correct_list_str_value, List[str]),
])
def test_request_python_value(correct_python_value, value_type):
    with OPENAI_SERVER_CALLER.mock([f'Here is the correct python value:\n{correct_python_value}\nShould be all good.'],
                                   record_more_if_needed=False):
        assert TestBasePythonValueProductsReviewGPT(value_type=value_type).get_value() == \
               eval(correct_python_value)


@pytest.mark.parametrize('non_correct_python_value, correct_python_value, value_type, error_should_include', [
    (correct_dict_str_any_value.replace('}', ''), correct_dict_str_any_value, Dict[str, Any], "flanked by `{` and `}`"),
    (correct_dict_str_str_value.replace("'3'", '3'), correct_dict_str_str_value, Dict[str, str], "The dict values must be of type: <class 'str'>"),
    (non_correct_list_str_value, correct_list_str_value, List[str], "The values must be of type: <class 'str'>"),
])
def test_request_python_value_with_error(
        non_correct_python_value, correct_python_value, value_type, error_should_include):
    with OPENAI_SERVER_CALLER.mock(
            [f'Here is some wrong python value:\n{non_correct_python_value}\nLet me know if it is ok.',
             f'Here is the correct python value:\n{correct_python_value}\nShould be fine now.'],
            record_more_if_needed=False):
        latex_requester = TestBasePythonValueProductsReviewGPT(value_type=value_type)
        assert latex_requester.get_value() == eval(correct_python_value)
        error_message = latex_requester.conversation[3]
        assert error_should_include in error_message.content
