from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, Any, get_args, get_origin

from data_to_paper.exceptions import data_to_paperException


@dataclass
class WrongTypeException(data_to_paperException):
    """
    Raised when a value is of the wrong type.
    """
    message: str = ''

    def __str__(self):
        return self.message


def check_all_of_type(elements: Iterable, type_: type, description: str = ''):
    """
    Check if all elements are of a certain type.
    """
    for e in elements:
        validate_value_type(e, type_, description)


def check_all_of_types(elements: Iterable, types_: Iterable[type], description: str = ''):
    """
    Check if all elements are of their matching types.
    """
    for e, type_ in zip(elements, types_):
        validate_value_type(e, type_, description)


def validate_value_type(value: Any, type_: type, description: str = ''):
    """
    Validate that the response is given in the correct format. if not raise TypeError.
    """
    if description:
        description = ' ' + description
    origin_type = get_origin(type_)
    if origin_type is None:
        origin_type = type_
    if origin_type is Any:
        return
    if not isinstance(value, origin_type):
        raise WrongTypeException(f'object{description} must be of type `{origin_type.__name__}`')

    child_types = get_args(type_)
    if not child_types:
        return
    if isinstance(value, dict):
        check_all_of_type(value.keys(), child_types[0], f'within the dict keys{description}')
        check_all_of_type(value.values(), child_types[1], f'within the dict values{description}')
    elif isinstance(value, (list, set)) and len(child_types) == 1:
        check_all_of_type(value, child_types[0], f'within the {type(value).__name__}{description}')
    elif isinstance(value, tuple) and len(child_types) == len(value):
        check_all_of_types(value, child_types, f'within the tuple{description}')
    else:
        raise NotImplementedError(f'format_type: {type(value)} is not implemented')
