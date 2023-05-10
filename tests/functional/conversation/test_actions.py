from _pytest.fixtures import fixture

from scientistgpt import Message, Role
from scientistgpt.conversation.conversation_actions import AppendMessage, AppendChatgptResponse, \
    FailedChatgptResponse, CopyMessagesBetweenConversations, CreateConversation, \
    NullConversationAction, RegenerateLastResponse, ResetToTag, DeleteMessages, ReplaceLastResponse

from scientistgpt.conversation.converation_manager import ConversationManager
from scientistgpt.conversation.message_designation import RangeMessageDesignation


@fixture()
def user_message():
    return Message(Role.USER, 'How much is 2 + 3 ?', 'math question')


@fixture()
def assistant_message():
    return Message(Role.ASSISTANT, 'The answer is 5.', 'answer')


def test_create_conversation(actions, conversations):
    action = CreateConversation(
        conversations=conversations,
        comment='this is a test', conversation_name='new_conversation',
        participants={'user', 'assistant'},
    )
    actions.apply_action(action)
    assert conversations.get_conversation('new_conversation') is not None


def test_append_message(actions_and_conversations, conversation, user_message):
    action = AppendMessage(
        conversations=actions_and_conversations.conversations,
        conversation_name=conversation.conversation_name,
        message=user_message, comment='this is a test')
    print('\n' + action.pretty_repr())
    action.apply()
    assert conversation[-1] is user_message


def test_add_chatgpt_response(conversations, conversation, assistant_message):
    action = AppendChatgptResponse(
        conversations=conversations,
        conversation_name=conversation.conversation_name,
        message=assistant_message, comment='this is a test',
        hidden_messages=[1, 3])
    print('\n' + action.pretty_repr())
    action.apply()
    assert conversation[-1] is assistant_message


def test_failed_chatgpt_response(conversations, conversation, assistant_message):
    original_length = len(conversation)
    action = FailedChatgptResponse(conversations=conversations, conversation_name=conversation.conversation_name,
                                   comment='this is a test', hidden_messages=-1)
    print('\n' + action.pretty_repr())
    action.apply()
    assert len(conversation) == original_length


def test_no_action(conversations, conversation):
    original_length = len(conversation)
    action = NullConversationAction(conversations=conversations,
                                    conversation_name=conversation.conversation_name, comment='no action was taken')
    print('\n' + action.pretty_repr())
    action.apply()
    assert len(conversation) == original_length


def test_regenerate_last_response(conversations, conversation, assistant_message):
    conversation.pop(-1)  # so that we have an assistant message last, to regenerate
    original_length = len(conversation)
    action = RegenerateLastResponse(conversations=conversations,
                                    conversation_name=conversation.conversation_name,
                                    comment='this is a test', hidden_messages=[1, 3],
                                    message=assistant_message)
    print('\n' + action.pretty_repr())
    action.apply()
    assert len(conversation) == original_length
    conversation[-1] = assistant_message


def test_reset_to_tag(conversations, conversation, assistant_message):
    assert len(conversation) == 4, "sanity"
    action = ResetToTag(conversations=conversations,
                        conversation_name=conversation.conversation_name,
                        comment='we are going back', tag='write_code')
    print('\n' + action.pretty_repr())
    action.apply()
    assert len(conversation) == 2


def test_delete_messages(conversations, conversation, assistant_message):
    expected = conversation[0::2]
    action = DeleteMessages(conversations=conversations,
                            conversation_name=conversation.conversation_name,
                            message_designation=['write_code', -1])
    print('\n' + action.pretty_repr())
    action.apply()
    conversation.print_all_messages()
    assert conversation == expected


def test_replace_last_response(conversations, conversation, assistant_message):
    conversation.append(Message(Role.ASSISTANT, 'bad response. to be replaced'))
    expected = conversation[:-1] + [assistant_message]
    action = ReplaceLastResponse(conversations=conversations,
                                 conversation_name=conversation.conversation_name,
                                 message=assistant_message, comment='this is a test')
    print('\n' + action.pretty_repr())
    action.apply()
    assert conversation == expected


def test_copy_messages_between_conversations(conversations, actions_and_conversations):
    manager = ConversationManager(conversation_name='conversation_1',
                                  actions_and_conversations=actions_and_conversations)
    manager.create_conversation()
    manager.append_system_message('You are a helpful assistant.')
    manager.append_user_message('Write a short code.', 'write_code')
    conversation1 = manager.conversation

    manager.conversation_name = 'conversation_2'
    manager.create_conversation()
    conversation2 = manager.conversation

    assert conversation1 != conversation2, "sanity"
    action = CopyMessagesBetweenConversations(
        conversations=conversations,
        conversation_name='conversation_2',
        source_conversation_name='conversation_1',
        message_designation=RangeMessageDesignation.from_(0, -1))
    print('\n' + action.pretty_repr())
    action.apply()
    assert conversation1 == conversation2
