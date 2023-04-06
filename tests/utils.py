from contextlib import contextmanager

from scientistgpt import Message
from scientistgpt.conversation import conversation


@contextmanager
def mock_openai(response):
    index = -1

    def mock_chatgpt_response(messages: list[Message]):
        nonlocal index
        index += 1
        if isinstance(response[index], Exception):
            raise response[index]
        return response[index]

    original_method = conversation._get_chatgpt_response
    conversation._get_chatgpt_response = mock_chatgpt_response
    yield
    conversation._get_chatgpt_response = original_method
