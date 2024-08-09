from __future__ import annotations

import time
from dataclasses import dataclass
from typing import List, Union, Callable
from typing import TYPE_CHECKING

import openai
import tiktoken

from data_to_paper.env import LLM_MODELS_TO_API_KEYS_AND_BASE_URL, CHOSEN_APP, FAKE_REQUEST_HUMAN_RESPONSE_ON_PLAYBACK
from data_to_paper.exceptions import TerminateException
from data_to_paper.interactive import HumanAction, BaseApp
from data_to_paper.utils.print_to_file import print_and_log_red, print_and_log
from data_to_paper.utils.serialize import SerializableValue, deserialize_serializable_value
from data_to_paper.utils.text_formatting import dedent_triple_quote_str
from data_to_paper.conversation.stage import Stage

from .base_server import OrderedKeyToListServerCaller
from .json_dump import dump_to_json, load_from_json
from .model_engine import ModelEngine
from .serialize_exceptions import serialize_exception, is_exception, de_serialize_exception

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


@dataclass
class LLMResponse(SerializableValue):
    """
    Class to store LLM response.
    value: str - the response from the LLM.
    """


class OpenaiServerCaller(OrderedKeyToListServerCaller):
    """
    Class to call OpenAI API.
    """
    file_extension = '_openai.txt'
    step_runner = None
    should_log_api_cost: bool = True

    def mock(self, old_records=None, record_more_if_needed=True, fail_if_not_all_responses_used=True,
             should_save=False, file_path=None):
        self.should_log_api_cost = False
        return super().mock(old_records, record_more_if_needed, fail_if_not_all_responses_used, should_save, file_path)

    @staticmethod
    def _check_before_spending_money(messages: List[Message], model_engine: ModelEngine):
        while True:
            user_choice = input(dedent_triple_quote_str("""
            Please carefully check that you are willing to proceed with this LLM API call.
            We suggest reading the current ongoing conversation and especially the last USER message \t
            to understand the instructions we are sending to the LLM.
            If you are willing to proceed, please type Y, otherwise type N.
            Note: if you choose N, the program will immediately abort.
            """))

            if user_choice.lower() == 'n':
                raise UserAbort(reason="User chose to abort the program.")
            elif user_choice.lower() == 'y':
                break
            else:
                print_and_log_red('Invalid input. Please choose Y/N.', should_log=False)

    @staticmethod
    def _check_after_spending_money(content: str, messages: List[Message], model_engine: ModelEngine):
        tokens_in = count_number_of_tokens_in_message(messages, model_engine)
        tokens_out = count_number_of_tokens_in_message(content, model_engine)
        pricing_in, pricing_out = model_engine.pricing
        print_and_log_red(f'Total: {tokens_in} prompt tokens, {tokens_out} returned tokens, '
                          f'cost: ${(tokens_in * pricing_in + tokens_out * pricing_out) :.2f}.',
                          should_log=False)

    def _log_api_usage_cost(self, content, messages: List[Message], model_engine: ModelEngine):
        tokens_in = count_number_of_tokens_in_message(messages, model_engine)
        tokens_out = count_number_of_tokens_in_message(content, model_engine)
        pricing_in, pricing_out = model_engine.pricing
        api_usage_cost = load_from_json(self.file_path.parents[0] / 'api_usage_cost.json')
        api_usage_cost[self.step_runner.current_stage.name] += tokens_in * pricing_in + tokens_out * pricing_out
        dump_to_json(api_usage_cost, self.file_path.parents[0] / 'api_usage_cost.json')

    def set_step_runner(self, step_runner):
        self.step_runner = step_runner

    def _generate_key(self, args, kwargs):
        if self.step_runner is None:
            return "GENERAL"
        return self.step_runner.current_stage.name

    def get_server_response(self, *args, **kwargs) -> Union[LLMResponse, HumanAction, Exception]:
        """
        returns the response from the server after post-processing. allows recording and replaying.
        """
        action = super().get_server_response(*args, **kwargs)
        if isinstance(action, str):
            action = LLMResponse(action)  # Backward compatibility
        if args[0] and self.should_log_api_cost:
            self._log_api_usage_cost(action.value, args[0], kwargs['model_engine'])
            self.step_runner.app_send_api_usage_cost()
        return action

    def _get_server_response(self, messages: List[Message], model_engine: Union[ModelEngine, Callable], **kwargs
                             ) -> Union[LLMResponse, HumanAction, Exception]:
        """
        Connect with openai to get response to conversation.
        """
        if not isinstance(model_engine, ModelEngine):
            # human action:
            return model_engine(messages, **kwargs)
        if CHOSEN_APP == 'console' or CHOSEN_APP == None:  # noqa (Mutable)
            # OpenaiServerCaller._check_before_spending_money(messages, model_engine)
            pass
        print_and_log_red('Calling the LLM-API for real.', should_log=False)

        api_key, api_base_url = LLM_MODELS_TO_API_KEYS_AND_BASE_URL[model_engine] \
            if model_engine in LLM_MODELS_TO_API_KEYS_AND_BASE_URL \
            else LLM_MODELS_TO_API_KEYS_AND_BASE_URL[None]
        if api_key is None:
            raise ValueError(f'API key for {model_engine} is not defined.')
        openai.api_key = api_key
        openai.api_base = api_base_url
        for attempt in range(MAX_NUM_LLM_ATTEMPTS):
            try:
                # TODO: Need to implement timeout. Our current timeout_context() is not working on a Worker of Qt.
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
        self._check_after_spending_money(content, messages, model_engine)
        return LLMResponse(content)

    def reset_to_step(self, stage: Stage):
        """
        Reset the records and the api usage cost files to the records of the given stage
        """
        stage_class = stage.__class__

        keys_to_delete_in_old = []
        for key in self.old_records.keys():
            if stage_class[key] >= stage:
                keys_to_delete_in_old.append(key)
        for key in keys_to_delete_in_old:
            del self.old_records[key]

        keys_to_delete_in_new = []
        for key in self.new_records.keys():
            if stage_class[key] >= stage:
                keys_to_delete_in_new.append(key)
        for key in keys_to_delete_in_new:
            del self.new_records[key]
        self.save_records()

        # reset the api usage cost to the given stage
        api_usage_cost = load_from_json(self.file_path.parents[0] / 'api_usage_cost.json')
        keys_to_delete_in_api_usage_cost = []
        for key in api_usage_cost.keys():
            if stage_class[key] >= stage:
                keys_to_delete_in_api_usage_cost.append(key)
        for key in keys_to_delete_in_api_usage_cost:
            del api_usage_cost[key]
        dump_to_json(api_usage_cost, self.file_path.parents[0] / 'api_usage_cost.json')

    @staticmethod
    def _serialize_record(record: Union[SerializableValue, Exception]):
        if isinstance(record, Exception):
            return serialize_exception(record)
        if isinstance(record, SerializableValue):
            return record.serialize()
        raise ValueError(f'Cannot serialize record of type {type(record)}:\n{record}')

    @staticmethod
    def _deserialize_record(serialized_record):
        if is_exception(serialized_record):
            return de_serialize_exception(serialized_record)
        try:
            return deserialize_serializable_value(serialized_record)
        except ValueError:
            # compatible with previous versions:
            return LLMResponse(serialized_record)


OPENAI_SERVER_CALLER = OpenaiServerCaller()


def count_number_of_tokens_in_message(messages: Union[List[Message], str], model_engine: ModelEngine) -> int:
    """
    Count number of tokens in message using tiktoken.
    """
    if model_engine is None:
        model_engine = ModelEngine.DEFAULT
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
    if model_engine is None:
        model_engine = ModelEngine.DEFAULT
    if expected_tokens_in_response is None:
        expected_tokens_in_response = DEFAULT_EXPECTED_TOKENS_IN_RESPONSE
    tokens = count_number_of_tokens_in_message(messages, model_engine)
    if tokens + expected_tokens_in_response > model_engine.max_tokens:
        return TooManyTokensInMessageError(tokens, expected_tokens_in_response, model_engine)
    print_and_log_red(f'Using {model_engine} (max {model_engine.max_tokens} tokens) '
                      f'for {tokens} context tokens and {expected_tokens_in_response} expected tokens.')
    if tokens + expected_tokens_in_response < ModelEngine.DEFAULT.max_tokens and model_engine > ModelEngine.DEFAULT:
        print_and_log(f'WARNING: Consider using {ModelEngine.DEFAULT} (max {ModelEngine.DEFAULT.max_tokens} tokens).',
                      should_log=False)
    try:
        action = OPENAI_SERVER_CALLER.get_server_response(messages, model_engine=model_engine, **kwargs)
        if isinstance(action, HumanAction):
            err = 'Human action retrieved, instead of LLM response.'
            if CHOSEN_APP == None:  # noqa (Mutable)
                err += '\nRuns recorded without human actions should be replayed with the same settings\n' \
                       '(set CHOSEN_APP to value other than None)'
            raise ValueError(err)
        assert isinstance(action, LLMResponse)
        return action.value
    except openai.error.InvalidRequestError as e:
        # TODO: add here any other exception that can be addressed by changing the number of tokens
        #     or bump up the model engine
        if OPENAI_MAX_CONTENT_LENGTH_MESSAGE_CONTAINS in str(e):
            return e
        else:
            raise


def get_human_response(app: BaseApp, **kwargs) -> HumanAction:
    """
    Allow the user to edit a message and return the edited message.
    Return None if the user did not change the message.
    """
    is_playback = are_more_responses_available()
    if FAKE_REQUEST_HUMAN_RESPONSE_ON_PLAYBACK and is_playback:
        app.request_action(**kwargs)
    response = OPENAI_SERVER_CALLER.get_server_response(
        [], model_engine=lambda messages, **k: app.request_action(**k), **kwargs)
    if isinstance(response, LLMResponse) and CHOSEN_APP != None:  # noqa (Mutable)
        raise ValueError(f'LLM response retrieved, instead of human action.\n'
                         f'Runs recorded without human actions should be replayed with the same settings\n'
                         f'(CHOSEN_APP = None)')
    assert isinstance(response, HumanAction)
    return response


def are_more_responses_available() -> bool:
    """
    Check if there are more recorded responses available from openai.
    """
    return OPENAI_SERVER_CALLER.are_more_records_available()
