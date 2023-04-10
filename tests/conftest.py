from _pytest.fixtures import fixture

from scientistgpt.conversation.replay import clear_actions_and_conversations


@fixture(autouse=True)
def reset_conversations_and_actions():
    clear_actions_and_conversations()
