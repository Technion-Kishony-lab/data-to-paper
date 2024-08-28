from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Iterable, Any, get_args, get_origin, Union

from data_to_paper.exceptions import data_to_paperException


@dataclass
class WrongTypeException(data_to_paperException):
    """
    Raised when a value is of the wrong type.
    """
    message: str = ''

    def __str__(self):
        return self.message


def name_of_type(type_: type) -> str:
    """
    Get the name of the type.
    """
    return str(type_).replace('typing.', '').replace("<class '", '').replace("'>", '')


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


def check_of_any_of_types(element: Any, types_: Iterable[type], description: str = ''):
    """
    Check if the element is of any of the types.
    """
    for type_ in types_:
        try:
            validate_value_type(element, type_, description)
            return
        except WrongTypeException:
            pass
    raise WrongTypeException(
        f'object{description} must be of one of the types: {", ".join([name_of_type(t) for t in types_])}')


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
    child_types = get_args(type_)

    if origin_type is Union:
        check_of_any_of_types(value, child_types, description)
        return

    if origin_type.__name__ == '_empty':
        return

    if not isinstance(value, origin_type):
        raise WrongTypeException(f'object{description} must be of type `{name_of_type(origin_type)}`')

    if not child_types:
        return
    if isinstance(value, dict):
        check_all_of_type(value.keys(), child_types[0], f'within the dict keys{description}')
        check_all_of_type(value.values(), child_types[1], f'within the dict values{description}')
    elif isinstance(value, (list, set)) and len(child_types) == 1:
        check_all_of_type(value, child_types[0], f'within the {name_of_type(type(value))}{description}')
    elif isinstance(value, tuple) and len(child_types) == len(value):
        check_all_of_types(value, child_types, f'within the tuple{description}')
    elif isinstance(value, Iterable):
        check_all_of_type(value, child_types[0], f'within the iterable{description}')
    else:
        raise NotImplementedError(f'format_type: {type(value)} is not implemented')


def raise_on_wrong_func_argument_types(func, *args, **kwargs):
    """
    Uses the function signature to check if the arguments are of the correct type.
    Works generally on any func
    """
    sig = inspect.signature(func)
    bound = sig.bind(*args, **kwargs)
    bound.apply_defaults()
    msgs = []
    for name, value in bound.arguments.items():
        type_ = sig.parameters[name].annotation
        try:
            validate_value_type(value, type_, f'argument `{name}`')
        except WrongTypeException as e:
            msgs.append(str(e))
    if msgs:
        raise WrongTypeException('\n'.join(msgs))


def raise_on_wrong_func_argument_types_decorator(func):
    """
    Decorator for the raise_on_wrong_func_argument_types function.
    """
    def wrapper(*args, **kwargs):
        raise_on_wrong_func_argument_types(func, *args, **kwargs)
        return func(*args, **kwargs)
    return wrapper
