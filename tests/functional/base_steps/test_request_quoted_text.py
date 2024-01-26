from data_to_paper.base_steps import BaseProductsQuotedReviewGPT
from dataclasses import dataclass

import pytest

from data_to_paper.servers.chatgpt import OPENAI_SERVER_CALLER
from data_to_paper.servers.model_engine import ModelEngine

from .utils import TestProductsReviewGPT, check_wrong_and_right_responses


@dataclass
class TestBaseProductsQuotedReviewGPT(TestProductsReviewGPT, BaseProductsQuotedReviewGPT):
    pass


enclosed_text = "\nThis is the enclosed text\n"


def test_request_quoted_text():
    check_wrong_and_right_responses(
        responses=[f'Here is the text:\n```{enclosed_text}```\nShould be all good.'],
        requester=TestBaseProductsQuotedReviewGPT(),
        correct_value=enclosed_text)


@pytest.mark.parametrize('left, right', [
    ('```', ''),
    ('', ''),
])
def test_request_quoted_text_with_error(left, right):
    check_wrong_and_right_responses(
        responses=[f'Here is some wrongly enclosed test:\n'
                   f'{left}{enclosed_text}{right}\nCheck it.',
                   f'Now it is good:\n```{enclosed_text}```\n'],
        requester=TestBaseProductsQuotedReviewGPT(
            rewind_after_getting_a_valid_response=None,
            rewind_after_end_of_review=None,
        ),
        correct_value=enclosed_text,
        error_texts=("Now it is good",),
        error_message_number=4)


def test_request_quoted_text_bumps_model_to_more_context():
    with OPENAI_SERVER_CALLER.mock(
            ['I am starting to write, but fail in the middle: \n```\nthe secret recipe is\n',
             'Now, with more context, I can finish this though: \n```\nthe secret recipe is to add chocolate\n```'],
            record_more_if_needed=False):
        requester = TestBaseProductsQuotedReviewGPT(model_engine=ModelEngine.GPT35_TURBO)
        assert requester.run_dialog_and_get_valid_result() == '\nthe secret recipe is to add chocolate\n'

    # assert context as sent to the server:
    models_used = [h[1].get('model_engine', None) for h in OPENAI_SERVER_CALLER.args_kwargs_response_history]
    assert ModelEngine.DEFAULT.get_model_with_more_strength() != ModelEngine.DEFAULT.get_model_with_more_context()
    assert models_used == [ModelEngine.DEFAULT, ModelEngine.DEFAULT.get_model_with_more_context()]


def test_request_quoted_text_repost_correct_response_as_fresh():
    requester = TestBaseProductsQuotedReviewGPT()
    with OPENAI_SERVER_CALLER.mock([
            f'I am telling a long long story which is not really needed and only then send:\n```{enclosed_text}```\n'],
            record_more_if_needed=False):
        assert requester.run_dialog_and_get_valid_result() == enclosed_text
    assert len(requester.conversation) == 3

    # Response is reposted as fresh:
    assert 'Here is the' in requester.conversation[-1].content


def test_request_quoted_text_with_flanked_header():
    requester = TestBaseProductsQuotedReviewGPT()
    with OPENAI_SERVER_CALLER.mock([
            f'```The Header of the Paragraph```\n"""{enclosed_text}"""\n',
            f'sorry for the mistake here is the correctly flanked text:\n'
            f'```The Header of the Paragraph\n{enclosed_text}\n```'],
            record_more_if_needed=False):
        assert requester.run_dialog_and_get_valid_result() == f'The Header of the Paragraph\n{enclosed_text}\n'
    assert len(requester.conversation) == 3

    # Response is reposted as fresh:
    assert 'Here is the' in requester.conversation[-1].content
