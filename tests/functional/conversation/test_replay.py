from scientistgpt import Role
from scientistgpt.conversation.conversation_actions import AppendMessage, Message, AppendChatgptResponse
from scientistgpt.conversation.actions import APPLIED_ACTIONS, \
    save_actions_to_file, load_actions_from_file, clear_actions_and_conversations
from scientistgpt.conversation.converation_manager import ConversationManager
from scientistgpt.conversation.replay import replay_actions
from scientistgpt.conversation.store_conversations import CONVERSATION_NAMES_TO_CONVERSATIONS


def test_save_load_actions(tmpdir):
    APPLIED_ACTIONS.append(AppendMessage(conversation_name='default',
                                         message=Message(role=Role.USER, content='what is 2 + 3 ?')))
    APPLIED_ACTIONS.append(AppendChatgptResponse(conversation_name='default',
                                                 message=Message(role=Role.ASSISTANT, content='the answer is 5')))
    old_actions = APPLIED_ACTIONS.copy()
    save_actions_to_file(tmpdir.join('actions.pkl'))

    assert load_actions_from_file(tmpdir.join('actions.pkl')) == old_actions


def test_replay_actions(tmpdir):
    conversation_manager1 = ConversationManager(conversation_name='conversation1')
    conversation_manager2 = ConversationManager(conversation_name='conversation2')
    conversation_manager1.create_conversation()
    conversation_manager2.create_conversation()
    conversation_manager1.append_user_message('what is 2 + 3 ?')
    conversation_manager2.append_user_message('what is 10 - 3 ?')
    conversation_manager2.append_surrogate_message('the answer is 7')
    conversation_manager1.append_surrogate_message('the answer is 5')

    old_conversations = CONVERSATION_NAMES_TO_CONVERSATIONS.copy()
    assert len(old_conversations) == 2

    save_actions_to_file(tmpdir.join('actions.pkl'))
    clear_actions_and_conversations()
    assert CONVERSATION_NAMES_TO_CONVERSATIONS == {}, "sanity"

    replay_actions(tmpdir.join('actions.pkl'))
    assert CONVERSATION_NAMES_TO_CONVERSATIONS == old_conversations
