import pytest
from _pytest.fixtures import fixture

from scientistgpt.conversation.actions_and_conversations import ActionsAndConversations, Conversations, Actions
from scientistgpt.env import SAVE_INTERMEDIATE_LATEX


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
