from _pytest.fixtures import fixture

from scientistgpt import Message, Role
from scientistgpt.conversation.actions import AppendMessage, AppendChatgptResponse, FailedChatgptResponse, \
    NoAction, RegenerateLastResponse, ResetToTag, DeleteMessages, ReplaceLastResponse


@fixture()
def user_message():
    return Message(Role.USER, 'How much is 2 + 3 ?', 'math question')


@fixture()
def assistant_message():
    return Message(Role.ASSISTANT, 'The answer is 5.', 'answer')


def test_append_message(conversation, user_message):
    action = AppendMessage(message=user_message, agent='tester', comment='this is a test')
    action.apply(conversation)
    assert conversation[-1] is user_message
    print('\n' + action.pretty_repr(conversation_name='test_conversation'))


def test_add_chatgpt_response(conversation, assistant_message):
    action = AppendChatgptResponse(message=assistant_message, agent='tester', comment='this is a test', hidden_messages=[1, 3])
    action.apply(conversation)
    assert conversation[-1] is assistant_message
    print('\n' + action.pretty_repr(conversation_name='test_conversation'))


def test_failed_chatgpt_response(conversation, assistant_message):
    original_length = len(conversation)
    action = FailedChatgptResponse(agent='tester', comment='this is a test', hidden_messages=-1)
    action.apply(conversation)
    assert len(conversation) == original_length
    print('\n' + action.pretty_repr(conversation_name='test_conversation'))


def test_no_action(conversation):
    original_length = len(conversation)
    action = NoAction(agent='tester', comment='no action was taken')
    action.apply(conversation)
    assert len(conversation) == original_length
    print('\n' + action.pretty_repr(conversation_name='test_conversation'))


def test_regenerate_last_response(conversation, assistant_message):
    conversation.pop(-1)  # so that we have an assistant message last, to regenerate
    original_length = len(conversation)
    action = RegenerateLastResponse(agent='tester', comment='this is a test', hidden_messages=[1, 3], message=assistant_message)
    action.apply(conversation)
    assert len(conversation) == original_length
    conversation[-1] = assistant_message
    print('\n' + action.pretty_repr(conversation_name='test_conversation'))


def test_reset_to_tag(conversation, assistant_message):
    assert len(conversation) == 4,  "sanity"
    action = ResetToTag(agent='tester', comment='we are going back', tag='write_code')
    action.apply(conversation)
    assert len(conversation) == 1
    print('\n' + action.pretty_repr(conversation_name='test_conversation'))


def test_delete_messages(conversation, assistant_message):
    expected = conversation[0::2]
    action = DeleteMessages(message_designation=['write_code', -1])
    action.apply(conversation)
    conversation.print_all_messages()
    assert conversation == expected
    print('\n' + action.pretty_repr(conversation_name='test_conversation'))


def test_replace_last_response(conversation, assistant_message):
    conversation.append_assistant_message('bad response. to be replaced')
    expected = conversation[:-1] + [assistant_message]
    action = ReplaceLastResponse(message=assistant_message, agent='tester', comment='this is a test')
    action.apply(conversation)
    assert conversation == expected
    print('\n' + action.pretty_repr(conversation_name='test_conversation'))
