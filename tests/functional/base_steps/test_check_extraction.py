from typing import Tuple

from scientistgpt.base_steps import BaseProductsQuotedReviewGPT, CheckExtractionReviewBackgroundProductsConverser
from dataclasses import dataclass

import pytest

from scientistgpt.base_steps.dual_converser import ReviewDialogDualConverserGPT
from scientistgpt.base_steps.result_converser import Rewind
from scientistgpt.env import MAX_MODEL_ENGINE
from scientistgpt.servers.chatgpt import OPENAI_SERVER_CALLER
from scientistgpt.servers.openai_models import ModelEngine

from .utils import TestProductsReviewGPT, check_wrong_and_right_responses


@dataclass
class TestCheckExtractionReviewBackgroundProductsConverser(TestProductsReviewGPT,
                                                           CheckExtractionReviewBackgroundProductsConverser):
    product_fields_from_which_response_is_extracted: Tuple[str, ...] = ()
    max_reviewing_rounds: int = 0
    rewind_after_end_of_review: Rewind = Rewind.ACCUMULATE
    rewind_after_getting_a_valid_response: Rewind = Rewind.ACCUMULATE

    def _get_text_from_which_response_should_be_extracted(self) -> str:
        return '0.123, 0.236, 4.56e-04, 9876321, 4321'

    def _check_and_extract_result_from_self_response(self, response: str):
        response = self._check_extracted_numbers(response)
        return super()._check_and_extract_result_from_self_response(response)


correct_response = 'Correct extractions: 0.12, 0.23, 0.24, 24%, 0.00046, 9,876,000, 4{,}300'

correct_response_with_formula = 'The difference was [0.12 - 0.23 = -0.11].'
correct_response_with_formula_formatted = 'The difference was -0.11.'


def test_correct_extraction():
    requester = TestCheckExtractionReviewBackgroundProductsConverser()
    with OPENAI_SERVER_CALLER.mock([
        correct_response,
    ], record_more_if_needed=False):
        assert requester.run_dialog_and_get_valid_result() == correct_response


def test_wrong_extraction():
    requester = TestCheckExtractionReviewBackgroundProductsConverser()
    with OPENAI_SERVER_CALLER.mock([
        correct_response.replace('0.24', '0.25'),
        correct_response,
    ], record_more_if_needed=False):
        assert requester.run_dialog_and_get_valid_result() == correct_response
    assert '0.25' in requester.conversation[-2].content
    assert '0.12' not in requester.conversation[-2].content


def test_extraction_with_formula():
    requester = TestCheckExtractionReviewBackgroundProductsConverser()
    with OPENAI_SERVER_CALLER.mock([
        correct_response_with_formula_formatted,
        correct_response_with_formula,
    ], record_more_if_needed=False):
        assert requester.run_dialog_and_get_valid_result() == correct_response_with_formula_formatted
    assert '-0.11' in requester.conversation[-2].content
    assert '0.12' not in requester.conversation[-2].content
