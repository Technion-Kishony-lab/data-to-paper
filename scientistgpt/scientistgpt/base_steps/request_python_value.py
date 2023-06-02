from dataclasses import dataclass

from scientistgpt.base_steps.base_products_conversers import BaseProductsReviewGPT

from typing import Optional, Any, Dict, Tuple, get_args, Iterable, Set

from scientistgpt.base_steps.dual_converser import SelfResponseError
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
class BasePythonValueProductsReviewGPT(BaseProductsReviewGPT):
    """
    A base class for agents requesting chatgpt to write a python value (like a list of str, or dict).
    Option for reviewing the sections (set max_reviewing_rounds > 0).
    """
    value_type: type = None  # Only supports Dict[str, str] and List[str] for now.

    @property
    def parent_type(self) -> type:
        return get_origin(self.value_type)

    @property
    def child_types(self) -> Tuple[type, ...]:
        return get_args(self.value_type)

    def validate_variable_type(self, response_value):
        """
        Validate that the response is given in the correct format. if not raise TypeError.
        """
        if not isinstance(response_value, self.parent_type):
            raise TypeError(f'object is not of type: {self.parent_type}')
        if isinstance(response_value, dict):
            if not check_all_of_type(response_value.keys(), self.child_types[0]):
                raise TypeError(f'The dict keys must be of type: {self.child_types[0]}')
            if not check_all_of_type(response_value.values(), self.child_types[1]):
                raise TypeError(f'The dict values must be of type: {self.child_types[1]}')
            return
        elif isinstance(response_value, (list, tuple, set)):
            if not check_all_of_type(response_value, self.child_types[0]):
                raise TypeError(f'The values must be of type: {self.child_types[0]}')
            return
        raise NotImplementedError(f'format_type: {self.value_type} is not implemented')

    def extract_python_value_from_response(self, response: str) -> Any:
        """
        Extracts a python value from chatgpt response.
        Returns the extracted value.
        If there is an error extracting the value, raise SelfResponseError is raised.
        """
        tags = TYPES_TO_TAG_PAIRS.get(self.parent_type)
        try:
            response = extract_text_between_tags(response, *tags, leave_tags=True)
        except ValueError:
            raise SelfResponseError(
                f'Your response should be formatted as a Python {self.parent_type.__name__}, '
                f'flanked by `{tags[0]}` and `{tags[1]}`.')
        try:
            response_value = eval(response)
        except Exception as e:
            raise SelfResponseError(
                f'I tried to eval your response with Python `eval(response)`, but got:\n{e}')
        try:
            self.validate_variable_type(response_value)
        except TypeError:
            raise SelfResponseError(
                f'Your response should be formatted as {self.value_type}.')
        return response_value

    def _check_response_value(self, response_value: Any) -> Any:
        """
        Check that the response value is valid.
        Return the value if it is valid, otherwise raise SelfResponseError if it is not valid.
        The returned value can also be modified.
        """
        return response_value

    def _check_and_extract_value_from_self_response(self, response: str):
        response_value = self.extract_python_value_from_response(response)
        response_value = self._check_response_value(response_value)
        self.returned_value = response_value


@dataclass
class PythonDictWithDefinedKeysProductsReviewGPT(BasePythonValueProductsReviewGPT):
    """
    A base class for agents requesting chatgpt to write a python dict, with specified keys.
    """
    requested_keys: Set[str] = None  # The keys that the dict should contain. `None` means any keys are allowed.

    def _check_response_value(self, response_value: Any) -> Optional[str]:
        """
        Check that the response value is valid.
        Return a feedback message if it is not valid, otherwise return None.
        """
        check_response_value = super()._check_response_value(response_value)
        if check_response_value is not None:
            return check_response_value
        if self.requested_keys is None:
            return None
        keys_in_response = set(response_value.keys())
        if keys_in_response != self.requested_keys:
            return f'Your response should contain the keys: {self.requested_keys}'

        return None
