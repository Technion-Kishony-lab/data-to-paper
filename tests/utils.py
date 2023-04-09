import functools
import inspect
import re
import os

from contextlib import contextmanager

from scientistgpt import Message, Conversation
from scientistgpt.conversation import conversation


@contextmanager
def mock_openai(responses):
    index = -1

    def mock_chatgpt_response(messages: list[Message]):
        nonlocal index
        index += 1
        if isinstance(responses[index], Exception):
            raise responses[index]
        return responses[index]

    original_method = conversation._get_chatgpt_response
    conversation._get_chatgpt_response = mock_chatgpt_response
    yield
    conversation._get_chatgpt_response = original_method


@contextmanager
def record_openai():
    index = -1
    original_method = conversation._get_chatgpt_response
    responses = []

    def record_chatgpt_response(messages: list[Message]):
        nonlocal index
        index += 1
        try:
            response = original_method(messages)
        except Exception as e:
            response = e
        responses.append(response)
        return response

    conversation._get_chatgpt_response = record_chatgpt_response
    yield responses
    conversation._get_chatgpt_response = original_method


def record_or_replay_openai(func):
    """
    Decorator to record or replay openai responses.

    If the file does not exist, then the decorated function will be called
    and the responses will be recorded to the file.

    If the file exists, then the responses will be read from the file and
    the decorated function will be called with the responses.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):

        test_file_path = os.path.abspath(inspect.getfile(func))
        test_dir = os.path.dirname(test_file_path)
        test_file = os.path.basename(test_file_path)
        file_path = os.path.join(test_dir, 'openai_responses', func.__name__ + '.txt')

        if not os.path.exists(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path))

        try:
            with open(file_path, 'r') as f:
                responses = re.findall(Conversation.SAVE_START + "(.*?)" + Conversation.SAVE_END, f.read(), re.DOTALL)
        except FileNotFoundError:
            with record_openai() as responses:
                func(*args, **kwargs)
            with open(file_path, 'w') as f:
                for response in responses:
                    f.write(f'{Conversation.SAVE_START}{response}{Conversation.SAVE_END}\n')
        else:
            with mock_openai(responses):
                func(*args, **kwargs)
    return wrapper
