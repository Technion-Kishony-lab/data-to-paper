import json
from dataclasses import dataclass

from data_to_paper import Message
from data_to_paper.base_steps.base_products_conversers import ReviewBackgroundProductsConverser

from typing import Any, Dict, Optional, get_origin, Collection, Iterable

from data_to_paper.base_steps.result_converser import Rewind
from data_to_paper.env import JSON_MODEL_ENGINE
from data_to_paper.run_gpt_code.code_utils import extract_content_of_triple_quote_block, FailedExtractingBlock, \
    NoBlocksFailedExtractingBlock, IncompleteBlockFailedExtractingBlock
from data_to_paper.servers.model_engine import ModelEngine
from data_to_paper.utils.nice_list import NiceDict
from data_to_paper.utils.tag_pairs import TagPairs
from data_to_paper.utils.check_type import validate_value_type, WrongTypeException
from data_to_paper.text.text_extractors import extract_text_between_most_flanking_tags
from data_to_paper.text import wrap_as_block

TYPES_TO_TAG_PAIRS: Dict[type, TagPairs] = {
    dict: TagPairs('{', '}'),
    list: TagPairs('[', ']'),
    tuple: TagPairs('(', ')'),
    set: TagPairs('{', '}'),
}


@dataclass
class PythonValueReviewBackgroundProductsConverser(ReviewBackgroundProductsConverser):
    """
    A base class for agents requesting the LLM to write a python value (like a list of str, or dict).
    Option for reviewing the sections (set max_reviewing_rounds > 0).
    """
    model_engine: ModelEngine = JSON_MODEL_ENGINE
    value_type: type = None
    rewind_after_getting_a_valid_response: Optional[Rewind] = Rewind.AS_FRESH
    json_mode: bool = False
    your_response_should_be_formatted_as: str = '{property_your_response_should_be_formatted_as}'

    @property
    def is_really_json_mode(self) -> bool:
        return self.json_mode and self.model_engine.allows_json_mode

    @property
    def python_or_json(self) -> str:
        return 'json' if self.json_mode else 'Python'

    @property
    def property_your_response_should_be_formatted_as(self) -> str:
        if self.json_mode:
            return f"a json object that can be evaluated with `json.loads()` to a Python {self.type_name}."
        return f"a Python {self.type_name} wrapped within a triple backtick 'python' code block."

    @property
    def parent_type(self) -> type:
        return get_origin(self.value_type)

    @property
    def type_name(self) -> str:
        return str(self.value_type).replace('typing.', '')

    def apply_get_and_append_assistant_message(self, *args, **kwargs) -> Message:
        kwargs['is_json'] = self.is_really_json_mode
        return super().apply_get_and_append_assistant_message(*args, **kwargs)

    def get_valid_result_as_markdown(self) -> str:
        return wrap_as_block(self.valid_result, 'python')

    def _check_response_and_get_extracted_text(self, response: str) -> str:
        """
        Extracts the string of the python value from LLM response.
        If there is an error extracting the value, _raise_self_response_error is called.
        """
        if self.is_really_json_mode:
            return response

        try:
            return extract_content_of_triple_quote_block(response, self.goal_noun, self.python_or_json)
        except NoBlocksFailedExtractingBlock:
            pass
        except FailedExtractingBlock as e:
            self._raise_self_response_error(
                title='# Failed to extract python block',
                error_message=str(e),
                missing_end=isinstance(e, IncompleteBlockFailedExtractingBlock))

        tags = TYPES_TO_TAG_PAIRS.get(self.parent_type)
        try:
            return extract_text_between_most_flanking_tags(response, *tags, keep_tags=True)
        except ValueError:
            self._raise_self_response_error(
                title='# Incorrect response format',
                error_message=f'Could not find a valid Python {self.type_name} in your response.',
                missing_end=tags[0] in response and tags[1] not in response)

    def _check_extracted_text_and_update_valid_result(self, extracted_text: str):
        response_value = self._evaluate_python_value_from_str(extracted_text)
        response_value = self._validate_value_type(response_value)
        response_value = self._check_response_value(response_value)
        self._update_valid_result(response_value)

    def _convert_extracted_text_to_fresh_looking_response(self, extracted_text: str) -> str:
        """
        Return a response that contains just the python value.
        """
        if self.is_really_json_mode:
            return extracted_text
        return wrap_as_block(extracted_text, self.python_or_json)

    def _evaluate_python_value_from_str(self, response: str) -> Any:
        try:
            if self.json_mode:
                return json.loads(response)
            else:
                return eval(response)
        except Exception as e:
            func = 'json.loads()' if self.json_mode else 'eval()'
            formatting_instructions = "{formatting_instructions_for_feedback}" + \
                f"I need to be able to just cut and paste it and evaluate with `{func}`."
            if not self.json_mode:
                formatting_instructions += "\nSo it has to be a valid Python value (not an assignment statement)."
            self._raise_self_response_error(
                title='# Incorrect response format',
                error_message=f'I tried to eval your response with Python `{func}`, but got:\n{e}\n',
                formatting_instructions=formatting_instructions
            )

    def _validate_value_type(self, response_value: Any) -> Any:
        """
        Validate that the response is given in the correct format. if not raise TypeError.
        """
        try:
            validate_value_type(response_value, self.value_type)
        except WrongTypeException as e:
            self._raise_self_response_error(
                title='# Incorrect response type',
                error_message=str(e))
        return response_value

    def _check_response_value(self, response_value: Any) -> Any:
        """
        Check that the response value is valid.
        Return the value if it is valid, otherwise call self._raise_self_response_error.
        The returned value can also be modified.
        """
        return response_value


@dataclass
class PythonDictReviewBackgroundProductsConverser(PythonValueReviewBackgroundProductsConverser):
    """
    A base class for agents requesting the LLM to write a python dict.
    """
    value_type: type = Dict[Any, Any]

    def _check_response_value(self, response_value: Any) -> Any:
        value = super()._check_response_value(response_value)
        return NiceDict(value)


@dataclass
class PythonDictWithDefinedKeysReviewBackgroundProductsConverser(PythonDictReviewBackgroundProductsConverser):
    """
    A base class for agents requesting the LLM to write a python dict, with specified keys.
    """
    requested_keys: Collection[str] = None  # The keys that the dict should contain. `None` means any keys are allowed.
    value_type: type = Dict[str, Any]

    def _check_response_value(self, response_value: Any) -> Any:
        """
        Check that the response value is valid.
        raise a feedback message if it is not valid.
        """
        check_response_value = super()._check_response_value(response_value)
        if self.requested_keys is not None:
            if set(response_value.keys()) != set(self.requested_keys):
                self._raise_self_response_error(
                    title='# Incorrect keys in response',
                    error_message=f'Your response should include a {self.python_or_json} dict containing the keys: '
                                  f'{self.requested_keys}')

        return check_response_value


@dataclass
class PythonDictWithDefinedKeysAndValuesReviewBackgroundProductsConverser(
        PythonDictWithDefinedKeysReviewBackgroundProductsConverser):
    allowed_values_for_keys: Dict[str, Iterable] = None  # The values that the dict may contain.

    def __post_init__(self):
        super().__post_init__()
        assert self.requested_keys is None
        self.requested_keys = self.allowed_values_for_keys.keys()

    def _check_response_value(self, response_value):
        check_response_value = super()._check_response_value(response_value)
        for key, value in response_value.items():
            if value not in self.allowed_values_for_keys[key]:
                self._raise_self_response_error(
                    title='# Incorrect values in python dict',
                    error_message=f'The value for key `{key}` should be one of: {self.allowed_values_for_keys[key]}')
        return check_response_value
