import time
import openai

from data_to_paper_new.chatgpt_client.chatgpt_models import ModelEngine
from data_to_paper_new.chatgpt_client.config import OPENAI_MODELS_TO_API_KEYS
from data_to_paper_new.roles.base_role import Role


DEFAULT_MAX_NUM_OPENAI_ATTEMPTS = 3
DEFAULT_SLEEP_BETWEEN_ATTEMPTS = 3

class ChatGptClient:
    """
    A client responsible for all communication with chat gpt
    """
    model: ModelEngine
    _api_key: str
    _max_request_attempts: int

    def __init__(self, model: ModelEngine, max_request_attempts: int = DEFAULT_MAX_NUM_OPENAI_ATTEMPTS):
        if model not in OPENAI_MODELS_TO_API_KEYS.keys():
            raise Exception("Not a valid model, missing api key in config")
        if not isinstance(max_request_attempts, int) or  max_request_attempts <= 0:
            raise Exception(f"max request attempts must be a number above zero, got {max_request_attempts}")

        self.model = model
        self._api_key = OPENAI_MODELS_TO_API_KEYS[model]
        self._max_request_attempts = max_request_attempts


    def get_response_for_messages(self, chatgpt_messages: list[dict]) -> str:
        """
        Connect with openai to get response to conversation.
        """
        openai.api_key = self._api_key
        for attempt in range(self._max_request_attempts):
            try:
                response = openai.ChatCompletion.create(
                    model=self.model.value,
                    messages=chatgpt_messages
                )
                break
            except openai.error.InvalidRequestError:
                raise
            except openai.error.OpenAIError as e:
                sleep_time = 1.0 * 2 ** attempt
                time.sleep(sleep_time)
                print(f'Retrying to call openai (attempt {attempt + 1}/{self._max_request_attempts}) ...')
        else:
            raise Exception(f'Failed to get response from OPENAI after {self._max_request_attempts} attempts.')

        content = response['choices'][0]['message']['content']

        return content



