import functools
import inspect
import re
import os

from contextlib import contextmanager
from pathlib import Path
from typing import Union

from scientistgpt import Message, Conversation, load_actions_from_file
from scientistgpt.conversation import conversation
from scientistgpt.conversation.actions import BaseChatgptResponse, AppendChatgptResponse


@contextmanager
def mock_openai(responses, record_more_from_openai_if_needed=False, fail_if_not_all_responses_used=True):
    def mock_chatgpt_response(messages: list[Message]):
        if not responses:
            if record_more_from_openai_if_needed:
                response = original_method(messages)
                new_responses.append(response)
            else:
                raise AssertionError('No more responses were mocked')
        else:
            response = responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    new_responses = []
    new_responses_and_exceptions = {'new_responses': new_responses, 'exception': None}
    original_method = conversation._get_chatgpt_response
    conversation._get_chatgpt_response = mock_chatgpt_response
    try:
        yield new_responses_and_exceptions
    except (Exception, KeyboardInterrupt) as e:
        new_responses_and_exceptions['exception'] = e
    finally:
        conversation._get_chatgpt_response = original_method
    if responses and fail_if_not_all_responses_used:
        raise AssertionError(f'Not all responses were used: {responses}')


@contextmanager
def mock_openai_from_saved_actions(filepath: Union[str, Path]):
    actions = load_actions_from_file(filepath)
    gpt_actions = [action for action in actions if isinstance(action, BaseChatgptResponse)]
    responses = [action.message if isinstance(action, AppendChatgptResponse) else action.exception
                 for action in gpt_actions]
    yield from mock_openai(responses)


@contextmanager
def record_openai():
    original_method = conversation._get_chatgpt_response
    responses = []

    def record_chatgpt_response(messages: list[Message]):
        try:
            response = original_method(messages)
        except Exception as e:
            response = e
        responses.append(response)
        return response

    conversation._get_chatgpt_response = record_chatgpt_response
    yield responses
    conversation._get_chatgpt_response = original_method


def record_or_replay_openai(file_path: Union[str, Path] = None, should_mock: bool = True):
    """
    Decorator to record or replay openai responses.

    If the file does not exist, then the decorated function will be called
    and the responses will be recorded to the file.

    If the file exists, then the responses will be read from the file and
    the decorated function will be called with the responses.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal file_path
            if not file_path:
                test_file_path = os.path.abspath(inspect.getfile(func))
                test_dir = os.path.dirname(test_file_path)
                file_path = os.path.join(test_dir, 'openai_responses', func.__name__ + '.txt')

            # Create the directory and file if not exist
            if not os.path.exists(os.path.dirname(file_path)):
                os.makedirs(os.path.dirname(file_path))

            if not os.path.isfile(file_path):
                with open(file_path, 'w') as f:
                    f.write('')

            # get previous responses (or empty list)
            with open(file_path, 'r') as f:
                responses = re.findall(Conversation.SAVE_START + "(.*?)" + Conversation.SAVE_END, f.read(), re.DOTALL)

            # run the test with the previous responses and record new responses
            with mock_openai(responses, record_more_from_openai_if_needed=True) as new_responses_and_exceptions:
                func(*args, **kwargs)

            # add new responses to the file
            if new_responses_and_exceptions['new_responses']:
                with open(file_path, 'a') as f:
                    for response in new_responses_and_exceptions['new_responses']:
                        f.write(f'{Conversation.SAVE_START}{response}{Conversation.SAVE_END}\n')

            # raise exception if there was one
            if new_responses_and_exceptions['exception']:
                raise new_responses_and_exceptions['exception']

        return wrapper if should_mock else func

    return decorator
