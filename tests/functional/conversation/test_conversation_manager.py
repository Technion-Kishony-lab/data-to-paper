from _pytest.fixtures import fixture

from scientistgpt import Message, Role
from scientistgpt.conversation.actions import RegenerateLastResponse, ReplaceLastResponse
from scientistgpt.conversation.converation_manager import ConversationManager
from scientistgpt.conversation.message_designation import RangeMessageDesignation
from tests.utils import mock_openai


@fixture()
def manager():
    manager = ConversationManager()
    manager.create_conversation()
    manager.append_system_message('You are a helpful assistant.')
    return manager


def test_conversation_manager_adding_messages(manager):
    with mock_openai([
        'The answer is 4',
    ]):
        manager.append_user_message('Hi, I am a user.')
        manager.append_provided_assistant_message('Hi, this is a predefined assistant response.')
        manager.append_user_message('How much is 2 + 2', tag='math question', comment='this is a math question')
        manager.append_commenter_message('This is a comment.')
        manager.get_and_append_assistant_message(tag='math answer')

    assert len(manager.get_conversation()) == 6
    assert manager.get_conversation().get_last_response() == 'The answer is 4'


def test_conversation_manager_regenerate_response(manager):
    with mock_openai([
        'The answer is ...',
        'The answer is 4',
    ]):
        manager.append_user_message('How much is 2 + 2', tag='math question', comment='this is a math question')
        manager.get_and_append_assistant_message(tag='math answer')
        manager.regenerate_previous_response()

    assert len(manager.get_conversation()) == 3
    assert len(manager.conversation_names_and_actions) == 4  # 3 actions
    assert manager.get_conversation()[-1] == Message(Role.ASSISTANT, 'The answer is 4', tag='math answer')


def test_conversation_manager_retry_response(manager, openai_exception):
    with mock_openai([
        openai_exception,
        'The answer is 4',
    ]):
        manager.append_user_message('Hi, I am a user.', comment='This message will be deleted when we regenerate')
        manager.append_provided_assistant_message('Hi, this is a predefined assistant response.')
        manager.append_user_message('How much is 2 + 2', tag='math question', comment='this is a math question')
        manager.get_and_append_assistant_message(tag='math answer')

    assert len(manager.get_conversation()) == 5
    assert len(manager.conversation_names_and_actions) == 6  # there is one more action, because one failed
    assert manager.get_conversation()[-1] == Message(Role.ASSISTANT, 'The answer is 4', tag='math answer')
    # message #1 was hidden after the first failed attempt:
    assert manager.conversation_names_and_actions[-1].action.hidden_messages == [1]


def test_conversation_manager_reset_to_tag_when_tag_repeats(manager):
    manager.append_user_message('Hi, I am a user.', tag='intro')
    manager.append_provided_assistant_message('Hi, this is a predefined assistant response.')
    assert len(manager.get_conversation()) == 3, "sanity"

    manager.append_user_message('Hi, I am a super user.', tag='intro')
    assert len(manager.get_conversation()) == 2


def test_conversation_manager_reset_to_tag(manager):
    assert len(manager.get_conversation()) == 1, "sanity"
    manager.append_user_message('Hi, I am a user.', tag='intro')
    manager.append_provided_assistant_message('Hi, this is a predefined assistant response.')
    assert len(manager.get_conversation()) == 3, "sanity"

    manager.reset_back_to_tag(tag='intro')
    assert len(manager.get_conversation()) == 1


def test_conversation_manager_delete_messages(manager):
    manager.append_user_message('m1')
    manager.append_user_message('m2', tag='tag2')
    manager.append_user_message('m3')
    manager.append_user_message('m4')
    manager.delete_messages(message_designation=RangeMessageDesignation.from_('tag2', -1))

    assert [m.content for m in manager.get_conversation()[1:]] == ['m1', 'm4']


def test_conversation_manager_replace_last_response(manager):
    manager.append_provided_assistant_message('preliminary message. to be replaced')
    original_len = len(manager.get_conversation())
    manager.replace_last_response('new response')
    assert manager.get_conversation().get_last_response() == 'new response'
    assert isinstance(manager.conversation_names_and_actions[-1].action, ReplaceLastResponse)
    assert len(manager.get_conversation()) == original_len
