from __future__ import annotations

import inspect
from dataclasses import dataclass
from functools import wraps
from typing import Iterable, Any, get_args, get_origin, Union, Tuple

from data_to_paper.exceptions import data_to_paperException


@dataclass
class WrongTypeException(data_to_paperException, TypeError):
    """
    Raised when a value is of the wrong type.
    """
    descriptions: Tuple[str, ...] = ()
    must_be: Union[type, str, Iterable[type]] = None
    found: Union[type, str] = None

    def get_found_description(self) -> str:
        if isinstance(self.found, type):
            return f'`{name_of_type(self.found)}`'
        return self.found

    def get_must_be_description(self) -> str:
        if isinstance(self.must_be, type):
            return f'of type `{name_of_type(self.must_be)}`'
        if isinstance(self.must_be, str):
            return self.must_be
        if isinstance(self.must_be, Iterable):
            return f"of one of the types: {', '.join([name_of_type(t) for t in self.must_be])}"
        raise NotImplementedError(f"must_be: {self.must_be}")

    @property
    def found_type(self) -> type:
        return type(self.found)

    def __str__(self):
        within = ''.join([' within the ' + d for d in self.descriptions])
        return (f"object{within} must be {self.get_must_be_description()} "
                f"(but found {self.get_found_description()})")


def name_of_type(type_: type) -> str:
    """
    Get the name of the type.
    """
    return str(type_).replace('typing.', '').replace("<class '", '').replace("'>", '')


def check_all_of_type(elements: Iterable, type_: type, descriptions: Tuple[str, ...] = ()):
    """
    Check if all elements are of a certain type.
    """
    for e in elements:
        validate_value_type(e, type_, descriptions)


def check_all_of_types(elements: Iterable, types_: Iterable[type], descriptions: Tuple[str, ...] = ()):
    """
    Check if all elements are of their matching types.
    """
    for e, type_ in zip(elements, types_):
        validate_value_type(e, type_, descriptions)


def check_of_any_of_types(element: Any, types_: Iterable[type], descriptions: Tuple[str, ...] = ()):
    """
    Check if the element is of any of the types.
    """
    for type_ in types_:
        try:
            validate_value_type(element, type_, descriptions)
            return
        except WrongTypeException:
            pass
    raise WrongTypeException(descriptions=descriptions, must_be=types_, found=type(element))


def validate_value_type(value: Any, type_: type, descriptions: Tuple[str, ...] = ()):
    """
    Validate that the response is given in the correct format. if not raise WrongTypeException.
    """
    origin_type = get_origin(type_)
    if origin_type is None:
        origin_type = type_
    if origin_type is Any:
        return
    child_types = get_args(type_)

    if origin_type is Union:
        check_of_any_of_types(value, child_types, descriptions)
        return

    if origin_type.__name__ == '_empty':
        return

    if not isinstance(value, origin_type):
        raise WrongTypeException(descriptions=descriptions, must_be=origin_type, found=type(value))

    if not child_types:
        return
    if isinstance(value, dict):
        check_all_of_type(value.keys(), child_types[0], ('dict keys', ) + descriptions)
        check_all_of_type(value.values(), child_types[1], ('dict values', ) + descriptions)
    elif isinstance(value, (list, set)) and len(child_types) == 1:
        check_all_of_type(value, child_types[0], (name_of_type(type(value)), ) + descriptions)
    elif isinstance(value, tuple):
        if len(child_types) == 2 and child_types[1] is Ellipsis:
            check_all_of_type(value, child_types[0], ('tuple', ) + descriptions)
        elif len(child_types) == len(value):
            check_all_of_types(value, child_types, ('tuple', ) + descriptions)
        else:
            raise WrongTypeException(descriptions=descriptions, must_be=f'a tuple of length {len(child_types)}',
                                     found=f'a tuple of length {len(value)}')
    elif isinstance(value, Iterable):
        check_all_of_type(value, child_types[0], ('iterable', ) + descriptions)
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
            validate_value_type(value, type_, (f'argument `{name}`', ))
        except WrongTypeException as e:
            msgs.append(str(e))
    if msgs:
        all_msgs = '\n'.join(msgs)
        raise TypeError(f"Error in arguments of {func.__name__}:\n{all_msgs}")


def raise_on_wrong_func_argument_types_decorator(func):
    """
    Decorator for the raise_on_wrong_func_argument_types function.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        raise_on_wrong_func_argument_types(func, *args, **kwargs)
        return func(*args, **kwargs)
    return wrapper
