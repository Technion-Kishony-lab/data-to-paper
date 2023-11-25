import json
from dataclasses import dataclass

from data_to_paper.base_steps.base_products_conversers import ReviewBackgroundProductsConverser

from typing import Any, Dict, Optional, get_origin, Collection, Iterable

from data_to_paper.base_steps.result_converser import Rewind
from data_to_paper.run_gpt_code.code_utils import extract_content_of_triple_quote_block, FailedExtractingBlock, \
    NoBlocksFailedExtractingBlock
from data_to_paper.utils import extract_text_between_tags
from data_to_paper.utils.nice_list import NiceDict
from data_to_paper.utils.tag_pairs import TagPairs
from data_to_paper.utils.check_type import validate_value_type, WrongTypeException

TYPES_TO_TAG_PAIRS: Dict[type, TagPairs] = {
    dict: TagPairs('{', '}'),
    list: TagPairs('[', ']'),
    tuple: TagPairs('(', ')'),
    set: TagPairs('{', '}'),
}


@dataclass
class PythonValueReviewBackgroundProductsConverser(ReviewBackgroundProductsConverser):
    """
    A base class for agents requesting chatgpt to write a python value (like a list of str, or dict).
    Option for reviewing the sections (set max_reviewing_rounds > 0).
    """
    value_type: type = None
    rewind_after_getting_a_valid_response: Optional[Rewind] = Rewind.REPOST_AS_FRESH
    json_mode: bool = False

    def __post_init__(self):
        super().__post_init__()
        if self.json_mode:
            self.chatgpt_parameters['response_format'] = {"type": "json_object"}

    @property
    def parent_type(self) -> type:
        return get_origin(self.value_type)

    def _get_fresh_looking_response(self, response) -> str:
        """
        Return a response that contains just the python value.
        """
        if self.json_mode:
            return super()._get_fresh_looking_response(response)
        response = self.returned_result
        return super()._get_fresh_looking_response(f"```python\n{response}\n```")

    def _check_and_extract_result_from_self_response(self, response: str):
        response_value_str = self._extract_str_of_python_value_from_response(response)
        response_value = self._evaluate_python_value_from_str(response_value_str)
        response_value = self._validate_value_type(response_value)
        response_value = self._check_response_value(response_value)
        self.returned_result = response_value

    def _extract_str_of_python_value_from_response(self, response: str) -> str:
        """
        Extracts the string of the python value from chatgpt response.
        If there is an error extracting the value, _raise_self_response_error is called.
        """
        if self.json_mode:
            return response

        try:
            return extract_content_of_triple_quote_block(response, self.goal_noun, 'python')
        except NoBlocksFailedExtractingBlock:
            pass
        except FailedExtractingBlock as e:
            self._raise_self_response_error(
                f'{e}\n'
                f'Your response should be formatted as a Python {self.parent_type.__name__}, '
                f'within a triple backtick code block.',
                rewind=Rewind.ACCUMULATE,
                bump_model=True)

        tags = TYPES_TO_TAG_PAIRS.get(self.parent_type)
        try:
            return extract_text_between_tags(response, *tags, keep_tags=True)
        except ValueError:
            self._raise_self_response_error(
                f'Your response should be formatted as a Python {self.parent_type.__name__}, '
                f'flanked by `{tags[0]}` and `{tags[1]}`.',
                bump_model=tags[0] in response and tags[1] not in response)

    def _evaluate_python_value_from_str(self, response: str) -> Any:
        if self.json_mode:
            try:
                return json.loads(response)
            except Exception as e:
                self._raise_self_response_error(
                    f'I tried to load your response with Python `json.loads()`, but got:\n{e}\n'
                    f'Your response should be a valid JSON value.')
        try:
            return eval(response)
        except Exception as e:
            self._raise_self_response_error(
                f'I tried to eval your response with Python `eval()`, but got:\n{e}\n'
                f'Your response should be formatted as a Python {self.parent_type.__name__} value '
                f'(not an assignment, and with no comments, etc) '
                f'that I can cut and paste and evaluated as is with `eval()`')

    def _validate_value_type(self, response_value: Any) -> Any:
        """
        Validate that the response is given in the correct format. if not raise TypeError.
        """
        try:
            validate_value_type(response_value, self.value_type)
        except WrongTypeException as e:
            self._raise_self_response_error(e.message)
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
    A base class for agents requesting chatgpt to write a python dict.
    """
    value_type: type = Dict[Any, Any]

    def _check_response_value(self, response_value: Any) -> Any:
        value = super()._check_response_value(response_value)
        return NiceDict(value)


@dataclass
class PythonDictWithDefinedKeysReviewBackgroundProductsConverser(PythonDictReviewBackgroundProductsConverser):
    """
    A base class for agents requesting chatgpt to write a python dict, with specified keys.
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
                    f'Your response should include a single Python dict containing the keys: {self.requested_keys}')

        return check_response_value


@dataclass
class PythonDictWithDefinedKeysAndValuesReviewBackgroundProductsConverser(
        PythonDictWithDefinedKeysReviewBackgroundProductsConverser):
    allowed_values_for_keys: Dict[str, Iterable] = None  # The values that the dict may contain.
    is_new_conversation: bool = False
    rewind_after_getting_a_valid_response: Rewind = Rewind.ACCUMULATE

    def __post_init__(self):
        super().__post_init__()
        assert self.requested_keys is None
        self.requested_keys = self.allowed_values_for_keys.keys()

    def _check_response_value(self, response_value):
        check_response_value = super()._check_response_value(response_value)
        for key, value in response_value.items():
            if value not in self.allowed_values_for_keys[key]:
                self._raise_self_response_error(
                    f'The value for key `{key}` should be one of: {self.allowed_values_for_keys[key]}')
        return check_response_value
