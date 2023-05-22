from _pytest.fixtures import fixture

from scientistgpt import Message, Role
from scientistgpt.conversation.conversation_actions import ReplaceLastResponse
from scientistgpt.conversation.conversation_manager import ConversationManager
from scientistgpt.servers.chatgpt import OPENAI_SERVER_CALLER
from scientistgpt.conversation.message_designation import RangeMessageDesignation


@fixture()
def manager(actions_and_conversations):
    manager = ConversationManager(actions_and_conversations=actions_and_conversations, conversation_name='test')
    manager.create_conversation()
    manager.append_system_message('You are a helpful assistant.')
    return manager


def test_conversation_manager_adding_messages(manager):
    with OPENAI_SERVER_CALLER.mock([
        'The answer is 4',
    ]):
        manager.append_user_message('Hi, I am a user.')
        manager.append_surrogate_message('Hi, this is a predefined assistant response.')
        manager.append_user_message('How much is 2 + 2', tag='math question', comment='this is a math question')
        manager.append_commenter_message('This is a comment.')
        manager.get_and_append_assistant_message(tag='math answer')

    assert len(manager.conversation) == 6
    assert manager.conversation.get_last_response() == 'The answer is 4'


@OPENAI_SERVER_CALLER.record_or_replay()
def test_conversation_manager_adding_messages_with_kwargs(manager):
    manager.append_user_message('Hi, I am a user.')
    manager.append_surrogate_message('Hi, this is a predefined assistant response.')
    manager.append_user_message("""                       
            Please choose one of the following options:

            a. I really like the number one.

            b. I think that number two is very nice.

            c. Number three is beautiful.

            Answer with just the number of the option you choose (only type a single character: "a", "b" or "c")
            Since it's just a dummy question to see if I can transfer kwargs to my function you can reply with 
            any of the options.
            """)
    manager.get_and_append_assistant_message(temperature=0, max_tokens=1)

    assert len(manager.conversation) == 5
    assert manager.conversation.get_last_response() in ['a', 'b', 'c']


def test_conversation_manager_regenerate_response(manager, actions):
    with OPENAI_SERVER_CALLER.mock([
        'The answer is ...',
        'The answer is 4',
    ]):
        manager.append_user_message('How much is 2 + 2', tag='math question', comment='this is a math question')
        manager.get_and_append_assistant_message(tag='math answer')
        manager.regenerate_previous_response()

    assert len(manager.conversation) == 3
    assert len(actions) == 6
    assert manager.conversation[-1].content == 'The answer is 4'


def test_conversation_manager_retry_response(manager, actions, openai_exception):
    with OPENAI_SERVER_CALLER.mock([
        openai_exception,
        'The answer is 4',
    ]):
        manager.append_user_message('Hi, I am a user.', comment='This message will be deleted when we regenerate')
        manager.append_surrogate_message('Hi, this is a predefined assistant response.')
        manager.append_user_message('How much is 2 + 2', tag='math question', comment='this is a math question')
        manager.get_and_append_assistant_message(tag='math answer')

    assert len(manager.conversation) == 5
    assert len(actions) == 7  # 5 + create + failed
    assert manager.conversation[-1].content == 'The answer is 4'
    # message #1 was hidden after the first failed attempt:
    assert actions[-1].hidden_messages == [1]


def test_conversation_manager_reset_to_tag_when_tag_repeats(manager):
    manager.append_user_message('Hi, I am a user.', tag='intro')
    manager.append_surrogate_message('Hi, this is a predefined assistant response.')
    assert len(manager.conversation) == 3, "sanity"

    manager.append_user_message('Hi, I am a super user.', tag='intro')
    assert len(manager.conversation) == 2


def test_conversation_manager_reset_to_tag(manager):
    manager.append_user_message('Hi, I am a user.', tag='intro')
    assert len(manager.conversation) == 2, "sanity"
    manager.append_surrogate_message('Hi, this is a predefined assistant response.')
    assert len(manager.conversation) == 3, "sanity"

    manager.reset_back_to_tag(tag='intro')
    assert len(manager.conversation) == 2


def test_conversation_manager_delete_messages(manager):
    manager.append_user_message('m1')
    manager.append_user_message('m2', tag='tag2')
    manager.append_user_message('m3')
    manager.append_user_message('m4')
    manager.delete_messages(message_designation=RangeMessageDesignation.from_('tag2', -2))

    assert [m.content for m in manager.conversation[1:]] == ['m1', 'm4']


def test_conversation_manager_replace_last_response(manager, actions):
    manager.append_surrogate_message('preliminary message. to be replaced')
    original_len = len(manager.conversation)
    manager.replace_last_response('new response')
    assert manager.conversation.get_last_response() == 'new response'
    assert isinstance(actions[-1], ReplaceLastResponse)
    assert len(manager.conversation) == original_len


def test_conversation_manager_copy_messages_from_another_conversations(actions_and_conversations):
    manager1 = ConversationManager(actions_and_conversations=actions_and_conversations,
                                   conversation_name='conversation1')
    manager1.create_conversation()
    manager1.append_user_message('m1')
    manager1.append_user_message('m2', tag='tag2')
    manager1.append_user_message('m3')
    manager1.append_user_message('m4')

    manager2 = ConversationManager(actions_and_conversations=actions_and_conversations,
                                   conversation_name='conversation2')
    manager2.create_conversation()
    manager2.copy_messages_from_another_conversations(
        message_designation=RangeMessageDesignation.from_('tag2', -1),
        source_conversation=manager1.conversation,
    )
    assert [m.content for m in manager2.conversation] == ['m2', 'm3', 'm4']


def test_conversation_manager_adds_python_header(manager):
    with OPENAI_SERVER_CALLER.mock([
        'the code is:\n'
        '```\n'
        'print("hello world")\n'
        '```\n\n'
        'the output is:\n'
        '```\n'
        'hello world\n'
        '```\n',
    ]):
        content = manager.get_and_append_assistant_message(is_code=True).content
    assert content == 'the code is:\n```python\nprint("hello world")\n```\n\nthe output is:\n```\nhello world\n```\n'
