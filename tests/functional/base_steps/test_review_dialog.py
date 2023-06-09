from scientistgpt.base_steps import BaseProductsQuotedReviewGPT
from dataclasses import dataclass

import pytest

from scientistgpt.base_steps.dual_converser import ReviewDialogDualConverserGPT
from scientistgpt.env import MAX_MODEL_ENGINE
from scientistgpt.servers.chatgpt import OPENAI_SERVER_CALLER
from scientistgpt.servers.openai_models import ModelEngine

from .utils import TestProductsReviewGPT, check_wrong_and_right_responses


@dataclass
class TestReviewDialogDualConverserGPT(TestProductsReviewGPT, ReviewDialogDualConverserGPT):
    max_reviewing_rounds: int = 3
    termination_phrase: str = 'I hereby approve'
    pass


def test_review_cycle():
    requester = TestReviewDialogDualConverserGPT()
    with OPENAI_SERVER_CALLER.mock([
        'This is my first draft',
        'I suggest making improvements',
        'Thank you. Here is my improved version',
        'I hereby approve'
    ],
            record_more_if_needed=False):
        assert requester.run_dialog_and_get_valid_result() == 'Thank you. Here is my improved version'
    assert len(requester.conversation) == 3


def test_ambiguous_reviewer():
    requester = TestReviewDialogDualConverserGPT()
    with OPENAI_SERVER_CALLER.mock([
        'This is my first draft',
        'I suggest these many improvements. Yet, I hereby approve',
        'I hereby approve'
    ],
            record_more_if_needed=False):
        assert requester.run_dialog_and_get_valid_result() == 'This is my first draft'
    assert len(requester.conversation) == 3
