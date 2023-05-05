import openai
import re

from typing import List, Union

from g3pt.conversation.message_designation import GeneralMessageDesignation
from g3pt.env import MODEL_ENGINE
from g3pt.servers.base_server import ServerCaller
from g3pt.utils.tag_pairs import SAVE_TAGS
from g3pt.conversation.message import Message

# Set up the OpenAI API client
from g3pt.env import OPENAI_API_KEY
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
    def _get_server_response(messages: List[Message], **kw) -> str:
        """
        Connect with openai to get response to conversation.
        """
        response = openai.ChatCompletion.create(
            model=MODEL_ENGINE,
            messages=[message.to_chatgpt_dict() for message in messages],
            **kw,
        )
        return response['choices'][0]['message']['content']


OPENAI_SERVER_CALLER = OpenaiSeverCaller()


def try_get_chatgpt_response(conversation, hidden_messages: GeneralMessageDesignation = None,
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
        return OPENAI_SERVER_CALLER.get_server_response(messages, **kwargs)
    except openai.error.InvalidRequestError as e:
        return e
    except Exception:
        raise RuntimeError("Failed accessing openai.")
