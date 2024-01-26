from typing import Tuple, Optional

from data_to_paper.base_steps import CheckExtractionReviewBackgroundProductsConverser
from dataclasses import dataclass

from data_to_paper.base_steps.result_converser import Rewind

from data_to_paper.servers.chatgpt import OPENAI_SERVER_CALLER


from .utils import TestProductsReviewGPT


@dataclass
class TestCheckExtractionReviewBackgroundProductsConverser(TestProductsReviewGPT,
                                                           CheckExtractionReviewBackgroundProductsConverser):
    product_fields_from_which_response_is_extracted: Tuple[str, ...] = ()
    max_reviewing_rounds: int = 0
    rewind_after_end_of_review: Rewind = Rewind.ACCUMULATE
    rewind_after_getting_a_valid_response: Optional[Rewind] = Rewind.ACCUMULATE

    def _get_text_from_which_response_should_be_extracted(self) -> str:
        return '0.123, 0.236, 4.56e-04, 9876321, 4321'

    def _check_response_and_get_extracted_result(self, response: str):
        response = self._check_extracted_numbers(response)
        return super()._check_response_and_get_extracted_result(response)


correct_response = 'Correct extractions: 0.12, 0.23, 0.24, 24%, 0.00046, 9,876,000, 4{,}300'


def test_correct_extraction():
    requester = TestCheckExtractionReviewBackgroundProductsConverser()
    with OPENAI_SERVER_CALLER.mock([
        correct_response,
    ], record_more_if_needed=False):
        requester.run_dialog_and_get_valid_result()


def test_wrong_extraction():
    requester = TestCheckExtractionReviewBackgroundProductsConverser()
    with OPENAI_SERVER_CALLER.mock([
        correct_response.replace('0.24', '0.25'),
        correct_response,
    ], record_more_if_needed=False):
        requester.run_dialog_and_get_valid_result()
    assert '0.25' in requester.conversation[-2].content
    assert '0.12' not in requester.conversation[-2].content
