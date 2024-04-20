from _pytest.fixtures import fixture

from data_to_paper import Message, Role
from data_to_paper.conversation.conversation_actions import AppendMessage, AppendLLMResponse, \
    FailedLLMResponse, CreateConversation, \
    NullConversationAction, ResetToTag, DeleteMessages, ReplaceLastMessage


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


def test_add_llm_response(conversations, conversation, assistant_message):
    action = AppendLLMResponse(
        conversations=conversations,
        conversation_name=conversation.conversation_name,
        message=assistant_message, comment='this is a test',
        hidden_messages=[1, 3])
    print('\n' + action.pretty_repr())
    action.apply()
    assert conversation[-1] is assistant_message


def test_failed_llm_response(conversations, conversation, assistant_message):
    original_length = len(conversation)
    action = FailedLLMResponse(conversations=conversations, conversation_name=conversation.conversation_name,
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
    action = ReplaceLastMessage(conversations=conversations,
                                conversation_name=conversation.conversation_name,
                                message=assistant_message, comment='this is a test')
    print('\n' + action.pretty_repr())
    action.apply()
    assert conversation == expected
