from dataclasses import dataclass

from data_to_paper.base_steps.base_products_conversers import ReviewBackgroundProductsConverser

from typing import Any, Dict, Optional, get_origin, Collection

from data_to_paper.base_steps.result_converser import Rewind
from data_to_paper.utils import extract_text_between_tags
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
    value_type: type = None  # Only supports Dict[str, str] and List[str] for now.
    rewind_after_getting_a_valid_response: Optional[Rewind] = Rewind.REPOST_AS_FRESH

    @property
    def parent_type(self) -> type:
        return get_origin(self.value_type)

    def _get_fresh_looking_response(self, response) -> str:
        """
        Return a response that contains just the python value.
        """
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
        tags = TYPES_TO_TAG_PAIRS.get(self.parent_type)
        try:
            return extract_text_between_tags(response, *tags, leave_tags=True)
        except ValueError:
            self._raise_self_response_error(
                f'Your response should be formatted as a Python {self.parent_type.__name__}, '
                f'flanked by `{tags[0]}` and `{tags[1]}`.',
                bump_model=tags[0] in response and tags[1] not in response)

    def _evaluate_python_value_from_str(self, response: str) -> Any:
        try:
            return eval(response)
        except Exception as e:
            self._raise_self_response_error(
                f'I tried to eval your response with Python `eval()`, but got:\n{e}')

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
class PythonDictWithDefinedKeysReviewBackgroundProductsConverser(PythonValueReviewBackgroundProductsConverser):
    """
    A base class for agents requesting chatgpt to write a python dict, with specified keys.
    """
    requested_keys: Collection[str] = None  # The keys that the dict should contain. `None` means any keys are allowed.

    def _check_response_value(self, response_value: Any) -> Any:
        """
        Check that the response value is valid.
        raise a feedback message if it is not valid.
        """
        check_response_value = super()._check_response_value(response_value)
        if self.requested_keys is not None:
            if set(response_value.keys()) != set(self.requested_keys):
                self._raise_self_response_error(f'Your response should contain the keys: {self.requested_keys}')

        return check_response_value
