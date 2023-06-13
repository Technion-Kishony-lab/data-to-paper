from scientistgpt.base_steps import BaseProductsQuotedReviewGPT
from dataclasses import dataclass

import pytest

from scientistgpt.env import MAX_MODEL_ENGINE
from scientistgpt.servers.chatgpt import OPENAI_SERVER_CALLER
from scientistgpt.servers.openai_models import ModelEngine

from .utils import TestProductsReviewGPT, check_wrong_and_right_responses


@dataclass
class TestBaseProductsQuotedReviewGPT(TestProductsReviewGPT, BaseProductsQuotedReviewGPT):
    pass


enclosed_text = "\nThis is the enclosed text\n"


@pytest.mark.parametrize('quotes', ['"""', "'''", '```'])
def test_request_quoted_text(quotes):
    check_wrong_and_right_responses(
        responses=[f'Here is the text:\n{quotes}{enclosed_text}{quotes}\nShould be all good.'],
        requester=TestBaseProductsQuotedReviewGPT(),
        correct_value=enclosed_text)


@pytest.mark.parametrize('incorrect_quotes', [
    ('"""', ''),
    ('', ''),
])
def test_request_quoted_text_with_error(incorrect_quotes):
    check_wrong_and_right_responses(
        responses=[f'Here is some wrongly enclosed test:\n'
                   f'{incorrect_quotes[0]}{enclosed_text}{incorrect_quotes[1]}\nCheck it.',
                   f'Now it is good:\n```{enclosed_text}```\n'],
        requester=TestBaseProductsQuotedReviewGPT(
            rewind_after_getting_a_valid_response=None,
            rewind_after_end_of_review=None,
        ),
        correct_value=enclosed_text,
        error_texts=("enclosed within triple-backticks", ))


def test_request_quoted_text_bumps_model():
    with OPENAI_SERVER_CALLER.mock(
            ['I am not sending any enclosed text',
             'I am starting to write, but fails: \n```\nthe secret recipe is\n',
             'Now, as a bumped-up model, I can finish this though: \n```\nthe secret recipe is to add chocolate\n```'],
            record_more_if_needed=False):
        requester = TestBaseProductsQuotedReviewGPT(model_engine=ModelEngine.GPT35_TURBO)
        assert requester.run_dialog_and_get_valid_result() == '\nthe secret recipe is to add chocolate\n'

    # assert context as sent to the server:
    models_used = [h[1].get('model_engine', None) for h in OPENAI_SERVER_CALLER.args_kwargs_response_history]
    assert models_used == [ModelEngine.GPT35_TURBO, ModelEngine.GPT35_TURBO, MAX_MODEL_ENGINE]


def test_request_quoted_text_repost_correct_response_as_fresh():
    requester = TestBaseProductsQuotedReviewGPT()
    with OPENAI_SERVER_CALLER.mock([
            f'I am tell a long long story which is not really needed and only then send:\n"""{enclosed_text}"""\n'],
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
