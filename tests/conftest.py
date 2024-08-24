import pytest
from pytest import fixture

from data_to_paper.conversation.actions_and_conversations import ActionsAndConversations, Conversations, Actions
from data_to_paper.env import SAVE_INTERMEDIATE_LATEX, CHOSEN_APP, DELAY_CODE_RUN_CACHE_RETRIEVAL, \
    DELAY_SERVER_CACHE_RETRIEVAL, DEFAULT_HUMAN_REVIEW_TYPE
from data_to_paper.types import HumanReviewType


@pytest.fixture(scope="session", autouse=True)
def set_env():
    with CHOSEN_APP.temporary_set(None), \
            DEFAULT_HUMAN_REVIEW_TYPE.temporary_set(HumanReviewType.NONE), \
            DELAY_CODE_RUN_CACHE_RETRIEVAL.temporary_set(0), \
            DELAY_SERVER_CACHE_RETRIEVAL.temporary_set(0):
        yield


@fixture()
def actions_and_conversations() -> ActionsAndConversations:
    return ActionsAndConversations()


@fixture()
def conversations(actions_and_conversations) -> Conversations:
    return actions_and_conversations.conversations


@fixture()
def actions(actions_and_conversations) -> Actions:
    return actions_and_conversations.actions


@fixture()
def tmpdir_with_csv_file(tmpdir):
    csv_file = tmpdir.join('test.csv')
    csv_file.write('a,b,c\n1,2,3\n4,5,6')
    return tmpdir


@fixture(autouse=True)
def set_save_intermediate_latex_to_false():
    with SAVE_INTERMEDIATE_LATEX.temporary_set(False):
        yield
