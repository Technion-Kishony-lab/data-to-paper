from __future__ import annotations

import os
import time
from dataclasses import dataclass
from data_to_paper.utils.text_formatting import dedent_triple_quote_str

import openai

from typing import List, Union, Optional

import tiktoken

from data_to_paper.env import OPENAI_MODELS_TO_ORGANIZATIONS_API_KEYS_AND_API_BASE_URL
from data_to_paper.utils.print_to_file import print_and_log_red, print_and_log
from data_to_paper.run_gpt_code.timeout_context import timeout_context
from data_to_paper.exceptions import TerminateException

from .base_server import ListServerCaller
from .model_engine import ModelEngine

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from data_to_paper.conversation.message import Message


TIME_LIMIT_FOR_OPENAI_CALL = 300  # seconds
MAX_NUM_LLM_ATTEMPTS = 5
DEFAULT_EXPECTED_TOKENS_IN_RESPONSE = 500
OPENAI_MAX_CONTENT_LENGTH_MESSAGE_CONTAINS = 'maximum context length'
# a sub-string that indicates that an openai exception was raised due to the message content being too long


@dataclass
class TooManyTokensInMessageError(Exception):
    """
    Exception raised when the number of tokens in the message is too large.
    """
    tokens: int
    expected_tokens_in_response: int
    model_engine: ModelEngine

    def __str__(self):
        return f'Number of tokens in context ({self.tokens}) is too large. ' \
               f'Expected number of tokens in response: {self.expected_tokens_in_response}. ' \
               f'Maximum number of tokens for {self.model_engine}: {self.model_engine.max_tokens}.'


class UserAbort(TerminateException):
    pass


def _get_actual_model_engine(model_engine: Optional[ModelEngine]) -> ModelEngine:
    """
    Return the actual model engine to use for the given model engine.
    """
    return model_engine or ModelEngine.DEFAULT


class OpenaiSeverCaller(ListServerCaller):
    """
    Class to call OpenAI API.
    """
    file_extension = '_openai.txt'

    @staticmethod
    def _check_before_spending_money(messages: List[Message], model_engine: ModelEngine):
        if False and model_engine > ModelEngine.DEFAULT:
            while True:
                answer = input(f'CONFIRM USING {model_engine} (y/n): ').lower()
                if answer == 'y':
                    break
                elif answer == 'n':
                    raise UserAbort()
        print_and_log_red('Calling the LLM-API for real.', should_log=False)

    @staticmethod
    def _check_after_spending_money(content: str, messages: List[Message], model_engine: ModelEngine):
        tokens_in = count_number_of_tokens_in_message(messages, model_engine)
        tokens_out = count_number_of_tokens_in_message(content, model_engine)
        pricing_in, pricing_out = model_engine.pricing
        print_and_log_red(f'Total: {tokens_in} prompt tokens, {tokens_out} returned tokens, '
                          f'cost: ${(tokens_in * pricing_in + tokens_out * pricing_out) / 1000:.2f}.',
                          should_log=False)
        # time.sleep(6)

    @staticmethod
    def _get_server_response(messages: List[Message], model_engine: ModelEngine, **kwargs) -> str:
        """
        Connect with openai to get response to conversation.
        """
        if os.environ['CLIENT_SERVER_MODE'] == 'False':
            # while True:
            #     user_choice = input(dedent_triple_quote_str("""
            #     Please carefully check that you are willing to proceed with this LLM API call.
            #     We suggest reading the current ongoing conversation and especially the last USER message \t
            #     to understand the instructions we are sending to the LLM.
            #     If you are willing to proceed, please type Y, otherwise type N.
            #     Note: if you choose N, the program will immediately abort.
            #     """))
            #
            #     if user_choice.lower() == 'n':
            #         raise UserAbort(reason="User chose to abort the program.")
            #     elif user_choice.lower() == 'y':
            #         break
            #     else:
            #         print_and_log_red('Invalid input. Please choose Y/N.', should_log=False)

            OpenaiSeverCaller._check_before_spending_money(messages, model_engine)

        organization, api_key, api_base_url = OPENAI_MODELS_TO_ORGANIZATIONS_API_KEYS_AND_API_BASE_URL[model_engine] \
            if model_engine in OPENAI_MODELS_TO_ORGANIZATIONS_API_KEYS_AND_API_BASE_URL \
            else OPENAI_MODELS_TO_ORGANIZATIONS_API_KEYS_AND_API_BASE_URL[None]
        openai.api_key = api_key
        openai.api_base = api_base_url
        openai.organization = organization
        for attempt in range(MAX_NUM_LLM_ATTEMPTS):
            try:
                with timeout_context(TIME_LIMIT_FOR_OPENAI_CALL):
                    response = openai.ChatCompletion.create(
                        model=model_engine.value,
                        messages=[message.to_llm_dict() for message in messages],
                        **kwargs,
                    )
                break
            except openai.error.InvalidRequestError:
                raise
            except (openai.error.OpenAIError, TimeoutError) as e:
                sleep_time = 1.0 * 2 ** attempt
                print_and_log_red(f'Unexpected OPENAI error:\n{type(e)}\n{e}\n'
                                  f'Going to sleep for {sleep_time} seconds before trying again.',
                                  should_log=False)
                time.sleep(sleep_time)
                print_and_log_red(f'Retrying to call openai (attempt {attempt + 1}/{MAX_NUM_LLM_ATTEMPTS}) ...',
                                  should_log=False)
        else:
            raise Exception(f'Failed to get response from OPENAI after {MAX_NUM_LLM_ATTEMPTS} attempts.')

        content = response['choices'][0]['message']['content']
        OpenaiSeverCaller._check_after_spending_money(content, messages, model_engine)
        return content


OPENAI_SERVER_CALLER = OpenaiSeverCaller()


def count_number_of_tokens_in_message(messages: Union[List[Message], str], model_engine: ModelEngine) -> int:
    """
    Count number of tokens in message using tiktoken.
    """
    model_engine = _get_actual_model_engine(model_engine)
    try:
        encoding = tiktoken.encoding_for_model(model_engine.value)
    except KeyError:
        encoding = tiktoken.encoding_for_model(ModelEngine.GPT35_TURBO.value)
    if isinstance(messages, str):
        num_tokens = len(encoding.encode(messages))
    else:
        num_tokens = len(encoding.encode('\n'.join([message.content for message in messages])))

    return num_tokens


def try_get_llm_response(messages: List[Message],
                         model_engine: ModelEngine = None,
                         expected_tokens_in_response: int = None,
                         **kwargs) -> Union[str, Exception]:
    """
    Try to get a response from openai to a specified conversation.

    The conversation is sent to openai after removing comment messages and any messages indicated
    in `hidden_messages`.

    If getting a response is successful then return response string.
    If failed due to openai exception, return None.
    """
    if expected_tokens_in_response is None:
        expected_tokens_in_response = DEFAULT_EXPECTED_TOKENS_IN_RESPONSE
    model_engine = _get_actual_model_engine(model_engine)
    tokens = count_number_of_tokens_in_message(messages, model_engine)
    if tokens + expected_tokens_in_response > model_engine.max_tokens:
        return TooManyTokensInMessageError(tokens, expected_tokens_in_response, model_engine)
    print_and_log_red(f'Using {model_engine} (max {model_engine.max_tokens} tokens) '
                      f'for {tokens} context tokens and {expected_tokens_in_response} expected tokens.')
    if tokens + expected_tokens_in_response < ModelEngine.DEFAULT.max_tokens and model_engine > ModelEngine.DEFAULT:
        print_and_log(f'WARNING: Consider using {ModelEngine.DEFAULT} (max {ModelEngine.DEFAULT.max_tokens} tokens).',
                      should_log=False)

    try:
        return OPENAI_SERVER_CALLER.get_server_response(messages, model_engine=model_engine, **kwargs)
    except openai.error.InvalidRequestError as e:
        # TODO: add here any other exception that can be addressed by changing the number of tokens
        #     or bump up the model engine
        if OPENAI_MAX_CONTENT_LENGTH_MESSAGE_CONTAINS in str(e):
            return e
        else:
            raise
