from dataclasses import dataclass

from scientistgpt.base_steps.base_products_conversers import ReviewBackgroundProductsConverser

from typing import Any, Dict, Tuple, get_args, Iterable, Set

from scientistgpt.utils import extract_text_between_tags
from scientistgpt.utils.tag_pairs import TagPairs


TYPES_TO_TAG_PAIRS: Dict[type, TagPairs] = {
    dict: TagPairs('{', '}'),
    list: TagPairs('[', ']'),
    tuple: TagPairs('(', ')'),
    set: TagPairs('{', '}'),
}


def get_origin(t: type) -> type:
    """
    Get the origin of a type.

    For example, get_origin(List[str]) is list.
    """
    if hasattr(t, '__origin__'):
        return t.__origin__
    return t


def check_all_of_type(elements: Iterable, type_: type) -> bool:
    """
    Check if all elements in a list are of a certain type.
    """
    if type_ is Any:
        return True
    return all(isinstance(e, type_) for e in elements)


@dataclass
class PythonValueReviewBackgroundProductsConverser(ReviewBackgroundProductsConverser):
    """
    A base class for agents requesting chatgpt to write a python value (like a list of str, or dict).
    Option for reviewing the sections (set max_reviewing_rounds > 0).
    """
    value_type: type = None  # Only supports Dict[str, str] and List[str] for now.
    repost_valid_response_as_fresh: bool = True

    @property
    def parent_type(self) -> type:
        return get_origin(self.value_type)

    @property
    def child_types(self) -> Tuple[type, ...]:
        return get_args(self.value_type)

    def _get_fresh_looking_response(self, response) -> str:
        """
        Return a response that contains just the python value.
        """
        response = self.returned_result
        return super()._get_fresh_looking_response(str(response))

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
                f'flanked by `{tags[0]}` and `{tags[1]}`.')

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
        if not isinstance(response_value, self.parent_type):
            self._raise_self_response_error(f'object is not of type: {self.parent_type}')
        if isinstance(response_value, dict):
            if not check_all_of_type(response_value.keys(), self.child_types[0]):
                self._raise_self_response_error(f'The dict keys must be of type: {self.child_types[0]}')
            if not check_all_of_type(response_value.values(), self.child_types[1]):
                self._raise_self_response_error(f'The dict values must be of type: {self.child_types[1]}')
            return response_value
        elif isinstance(response_value, (list, tuple, set)):
            if not check_all_of_type(response_value, self.child_types[0]):
                self._raise_self_response_error(f'The values must be of type: {self.child_types[0]}')
            return response_value
        raise NotImplementedError(f'format_type: {self.value_type} is not implemented')

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
    requested_keys: Set[str] = None  # The keys that the dict should contain. `None` means any keys are allowed.

    def _check_response_value(self, response_value: Any) -> Any:
        """
        Check that the response value is valid.
        raise a feedback message if it is not valid.
        """
        check_response_value = super()._check_response_value(response_value)
        if self.requested_keys is not None:
            keys_in_response = set(response_value.keys())
            if keys_in_response != self.requested_keys:
                self._raise_self_response_error(f'Your response should contain the keys: {self.requested_keys}')

        return check_response_value
