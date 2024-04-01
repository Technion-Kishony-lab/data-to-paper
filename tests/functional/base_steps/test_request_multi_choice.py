from dataclasses import dataclass

import pytest

from data_to_paper import Role
from data_to_paper.base_steps import MultiChoiceBackgroundProductsConverser
from data_to_paper.servers.llm_call import OPENAI_SERVER_CALLER

from .utils import TestProductsReviewGPT, check_wrong_and_right_responses


@dataclass
class TestMultiChoiceBackgroundProductsConverser(TestProductsReviewGPT, MultiChoiceBackgroundProductsConverser):
    pass


correct_answer = "I choose option 2"


@pytest.mark.parametrize('correct_response, incorrect_response, expected_value, error_keywords', [
    (correct_answer, correct_answer.replace('2', '3'), '2', ('just a single character', '1', '2')),
    (correct_answer, correct_answer.replace('2', '1 and 2'), '2', ('just a single character', '1', '2')),
])
def test_request_multi_choice_incorrect_then_correct(correct_response, incorrect_response,
                                                     expected_value, error_keywords):
    check_wrong_and_right_responses(
        [incorrect_response, correct_response],
        requester=TestMultiChoiceBackgroundProductsConverser(rewind_after_getting_a_valid_response=None),
        correct_value=expected_value,
        error_message_number=3,
        error_texts=error_keywords)


def test_request_multi_choice_only_keeps_one_error_message():
    requester = TestMultiChoiceBackgroundProductsConverser()
    with OPENAI_SERVER_CALLER.mock(['nothing', 'something else', '1 and 2', '1'], record_more_if_needed=False):
        assert requester.run_and_get_valid_result() == '1'

    assert len(requester.conversation) == 3  # 2 SYSTEM, USER prompt, correct ASSISTANT answer
    assert requester.conversation[0].role == Role.SYSTEM
    assert 'Please choose' in requester.conversation[1].content
    assert requester.conversation[2].content == '1'

    # assert context as sent to the server:
    messages_lists = [h[0][0] for h in OPENAI_SERVER_CALLER.args_kwargs_response_history]
    assert [len(lst) for lst in messages_lists] == [2, 4, 4, 4]
    assert all('Answer with just' in lst[-1].content for lst in messages_lists[1:])
    assert [lst[-2].content for lst in messages_lists[1:]] == ['nothing', 'something else', '1 and 2']
