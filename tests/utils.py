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
from scientistgpt.gpt_interactors.citation_adding import citataion_utils


def mock_openai(responses, record_more_from_openai_if_needed=False, fail_if_not_all_responses_used=True):
    return mock_server(conversation, server_calling_func_name='_get_chatgpt_response', responses=responses,
                       record_more_from_server_if_needed=record_more_from_openai_if_needed,
                       fail_if_not_all_responses_used=fail_if_not_all_responses_used)


@contextmanager
def mock_server(module, server_calling_func_name: str,
                responses, record_more_from_server_if_needed=False, fail_if_not_all_responses_used=True):

    def mock_serve_response(*args, **kwargs):
        if not responses:
            if record_more_from_server_if_needed:
                response = original_method(*args, **kwargs)
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
    original_method = getattr(module, server_calling_func_name)
    setattr(module, server_calling_func_name, mock_serve_response)
    keyboard_interrupt_occurred = False
    try:
        yield new_responses_and_exceptions
    except (Exception, KeyboardInterrupt) as e:
        new_responses_and_exceptions['exception'] = e
        keyboard_interrupt_occurred = isinstance(e, KeyboardInterrupt)
    finally:
        setattr(module, server_calling_func_name, original_method)
    if fail_if_not_all_responses_used and responses and not keyboard_interrupt_occurred:
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
    return record_or_replay_server(module=conversation, server_calling_func_name='_get_chatgpt_response',
                                   file_path=file_path, should_mock=should_mock)


def record_or_replay_crossref(file_path: Union[str, Path] = None, should_mock: bool = True):
    return record_or_replay_server(module=citataion_utils, server_calling_func_name='crossref_search',
                                   file_path=file_path, should_mock=should_mock)


def record_or_replay_server(module, server_calling_func_name, file_path: Union[str, Path] = None, should_mock: bool = True):
    """
    Decorator to record or replay server responses.

    If the file does not exist, then the decorated function will be called
    and the responses will be recorded to the file.

    If the file exists, then the responses will be read from the file and
    the decorated function will be called with the responses.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal file_path

            # use the file path of the decorated function if not given
            if not file_path:
                test_file_path = os.path.abspath(inspect.getfile(func))
                test_dir = os.path.dirname(test_file_path)
                file_path = os.path.join(test_dir, 'openai_responses', func.__name__ + '.txt')

            # Create the directory and file if not exist
            if not os.path.exists(os.path.dirname(file_path)):
                os.makedirs(os.path.dirname(file_path))

            # create an empty response file if not exist
            if not os.path.isfile(file_path):
                with open(file_path, 'w') as f:
                    f.write('')

            # get previous responses (or empty list)
            with open(file_path, 'r') as f:
                responses = re.findall(Conversation.SAVE_START + "(.*?)" + Conversation.SAVE_END, f.read(), re.DOTALL)

            # run the test with the previous responses and record new responses
            with mock_server(
                    module=module,
                    server_calling_func_name=server_calling_func_name,
                    responses=responses,
                    record_more_from_server_if_needed=True) as new_responses_and_exceptions:
                func(*args, **kwargs)

            # add new responses, if any, to the responses file
            if new_responses_and_exceptions['new_responses']:
                with open(file_path, 'a') as f:
                    for response in new_responses_and_exceptions['new_responses']:
                        f.write(f'{Conversation.SAVE_START}{response}{Conversation.SAVE_END}\n')

            # raise exception if there was one
            if new_responses_and_exceptions['exception']:
                raise new_responses_and_exceptions['exception']

        return wrapper if should_mock else func

    return decorator
