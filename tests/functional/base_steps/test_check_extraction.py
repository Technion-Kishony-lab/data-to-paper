from typing import Tuple, Optional
from unittest.mock import Mock

from _pytest.fixtures import fixture

from data_to_paper.base_steps import CheckExtractionReviewBackgroundProductsConverser, \
    CheckReferencedNumericReviewBackgroundProductsConverser
from dataclasses import dataclass

from data_to_paper.base_steps.result_converser import Rewind

from data_to_paper.servers.llm_call import OPENAI_SERVER_CALLER

from .utils import TestProductsReviewGPT


@fixture()
def products():
    products = Mock()
    products.get_name = Mock(return_value='field 1')
    products.get_description_for_llm = Mock(
        return_value='Some numbers: \\hypertarget{A0}{0.123}, \\hypertarget{A1}{0.236}, \\hypertarget{A2}{4.56e-04}, '
                     '\\hypertarget{A3}{9876321}, \\hypertarget{A4}{4321}')
    products.is_product_available = Mock(return_value=True)
    return products


@dataclass
class TestCheckReferencedNumericReviewBackgroundProductsConverser(
        TestProductsReviewGPT, CheckReferencedNumericReviewBackgroundProductsConverser):
    background_product_fields: Tuple[str, ...] = ('field1', )
    product_fields_from_which_response_is_extracted: Tuple[str, ...] = ('field1', )
    max_reviewing_rounds: int = 0
    rewind_after_end_of_review: Rewind = Rewind.ACCUMULATE
    rewind_after_getting_a_valid_response: Optional[Rewind] = Rewind.ACCUMULATE

    def _check_response_and_get_extracted_text(self, response: str):
        response = self._check_extracted_numbers(response)
        return super()._check_response_and_get_extracted_text(response)


@fixture()
def numeric_converser(products):
    converser = TestCheckReferencedNumericReviewBackgroundProductsConverser()
    converser.products = products
    return converser


def test_referenced_based_numeric_converser(numeric_converser):
    with OPENAI_SERVER_CALLER.mock([
        'Incorrect extractions: '
        'No ref: 0.123, '
        'Wrong val: \\hyperlink{A1}{1.236}, '
        'Wrong ref: \\hyperlink{A9}{4.56e-04}, '
        'OK: \\hyperlink{A3}{9876321}, \\hyperlink{A4}{4321}',
        'Correct extractions: \\hyperlink{A3}{9876321}, \\hyperlink{A4}{4321}',
    ], record_more_if_needed=False):
        numeric_converser.run_and_get_valid_result()


@dataclass
class TestCheckExtractionReviewBackgroundProductsConverser(TestProductsReviewGPT,
                                                           CheckExtractionReviewBackgroundProductsConverser):
    product_fields_from_which_response_is_extracted: Tuple[str, ...] = ()
    max_reviewing_rounds: int = 0
    rewind_after_end_of_review: Rewind = Rewind.ACCUMULATE
    rewind_after_getting_a_valid_response: Optional[Rewind] = Rewind.ACCUMULATE

    def _get_text_from_which_response_should_be_extracted(self) -> str:
        return '0.123, 0.236, 4.56e-04, 9876321, 4321'

    def _check_response_and_get_extracted_text(self, response: str):
        response = self._check_extracted_numbers(response)
        return super()._check_response_and_get_extracted_text(response)


correct_response = 'Correct extractions: 0.12, 0.23, 0.24, 24%, 0.00046, 9,876,000, 4{,}300'


def test_correct_extraction():
    requester = TestCheckExtractionReviewBackgroundProductsConverser()
    with OPENAI_SERVER_CALLER.mock([
        correct_response,
    ], record_more_if_needed=False):
        requester.run_and_get_valid_result()


def test_wrong_extraction():
    requester = TestCheckExtractionReviewBackgroundProductsConverser()
    with OPENAI_SERVER_CALLER.mock([
        correct_response.replace('0.24', '0.25'),
        correct_response,
    ], record_more_if_needed=False):
        requester.run_and_get_valid_result()
    assert '0.25' in requester.conversation[-2].content
    assert '0.12' not in requester.conversation[-2].content
