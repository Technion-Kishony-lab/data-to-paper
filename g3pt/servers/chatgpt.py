import openai
import re

from typing import List, Union

from g3pt.conversation.message_designation import GeneralMessageDesignation
from g3pt.env import MAX_MODEL_ENGINE, DEFAULT_MODEL_ENGINE, OPENAI_API_KEY
from g3pt.utils.tag_pairs import SAVE_TAGS
from g3pt.conversation.message import Message

from .base_server import ServerCaller
from .openai_models import ModelEngine

# Set up the OpenAI API client
openai.api_key = OPENAI_API_KEY


class OpenaiSeverCaller(ServerCaller):
    """
    Class to call OpenAI API.
    """
    file_extension = '_openai.txt'

    @staticmethod
    def _save_records(file, records):
        for response in records:
            file.write(SAVE_TAGS.wrap(response) + '\n')

    @staticmethod
    def _load_records(file):
        return re.findall(SAVE_TAGS.wrap("(.*?)"), file.read(), re.DOTALL)

    @staticmethod
    def _get_server_response(messages: List[Message], model_engine: ModelEngine, **kwargs) -> str:
        """
        Connect with openai to get response to conversation.
        """
        model_engine = model_engine or DEFAULT_MODEL_ENGINE
        response = openai.ChatCompletion.create(
            model=min(MAX_MODEL_ENGINE, model_engine).value,
            messages=[message.to_chatgpt_dict() for message in messages],
            **kwargs,
        )
        return response['choices'][0]['message']['content']


OPENAI_SERVER_CALLER = OpenaiSeverCaller()


def try_get_chatgpt_response(conversation, hidden_messages: GeneralMessageDesignation = None,
                             model_engine: ModelEngine = None,
                             **kwargs) -> Union[str, Exception]:
    """
    Try to get a response from openai to a specified conversation.

    The conversation is sent to openai after removing comment messages and any messages indicated
    in `hidden_messages`.

    If getting a response is successful then return response string.
    If failed due to openai exception, return None.
    """
    indices_and_messages = conversation.get_chosen_indices_and_messages(hidden_messages)
    messages = [message for _, message in indices_and_messages]
    try:
        return OPENAI_SERVER_CALLER.get_server_response(messages, model_engine=model_engine, **kwargs)
    except openai.error.InvalidRequestError as e:
        return e
    except Exception:
        raise RuntimeError("Failed accessing openai.")
