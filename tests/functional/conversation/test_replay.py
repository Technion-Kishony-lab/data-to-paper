from data_to_paper import Role
from data_to_paper.conversation.conversation_actions import AppendMessage, Message, AppendChatgptResponse
from data_to_paper.conversation.conversation_manager import ConversationManager
from data_to_paper.conversation.replay import replay_actions


def test_save_load_actions(tmpdir, actions, conversations):
    actions.append(AppendMessage(
        conversations=conversations,
        conversation_name='default',
        message=Message(role=Role.USER, content='what is 2 + 3 ?')))
    actions.append(AppendChatgptResponse(
        conversations=conversations,
        conversation_name='default',
        message=Message(role=Role.ASSISTANT, content='the answer is 5')))
    old_actions = actions.copy()
    actions.save_actions_to_file(tmpdir.join('actions.pkl'))

    assert actions.load_actions_from_file(tmpdir.join('actions.pkl')) == old_actions


def test_replay_actions(tmpdir, actions, conversations, actions_and_conversations):
    conversation_manager1 = ConversationManager(actions_and_conversations=actions_and_conversations,
                                                conversation_name='conversation1')
    conversation_manager2 = ConversationManager(actions_and_conversations=actions_and_conversations,
                                                conversation_name='conversation2')
    conversation_manager1.create_conversation()
    conversation_manager2.create_conversation()
    conversation_manager1.append_user_message('what is 2 + 3 ?')
    conversation_manager2.append_user_message('what is 10 - 3 ?')
    conversation_manager2.append_surrogate_message('the answer is 7')
    conversation_manager1.append_surrogate_message('the answer is 5')

    old_conversations = conversations.copy()
    assert len(old_conversations) == 2

    actions.save_actions_to_file(tmpdir.join('actions.pkl'))
    actions.clear()

    replay_actions(tmpdir.join('actions.pkl'))
