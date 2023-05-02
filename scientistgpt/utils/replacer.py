import re

from contextlib import contextmanager
from dataclasses import dataclass


def with_attribute_replacement(func):
    """
    a decorator for methods of a Replacer class that should run while replacing attributes.
    """
    def wrapper(self, *args, **kwargs):
        with self.attributes_replacement():
            return func(self, *args, **kwargs)
    return wrapper


def format_str_while_preserving_curly_brackets(string: str, **kwargs):
    """
    Format a string while preserving curly brackets.
    For example:
    format_str_while_preserving_curly_brackets('hello {{KEEP ME}} {name}', name='john') == 'hello {{KEEP ME}} john'
    """
    for key, value in kwargs.items():
        string = re.sub(r"(?<!{){" + key + r"}(?!})", str(value), string)
    return string


def _super_getatter(self, name):
    return super(Replacer, self).__getattribute__(name)


def _super_get_is_replacing(self):
    return _super_getatter(self, 'is_replacing')


def _do_not_replace(self):
    """
    A context manager for temporarily not replacing attributes of a Replacer class.
    """
    return super(Replacer, self).__getattribute__('not_replacing_attributes')()


@dataclass
class Replacer:
    """
    Base class for dataclass classes that have specific str attributes that should be replaced base on the
    values of other attributes.

    name: str = 'john'
    greeting: str = 'hello {name}'
    REPLACED_ATTRS: str = ['greeting']
    ADDITIONAL_DICT_ATTRS: str = ['name']
    """

    is_replacing: bool = False

    REPLACED_ATTRS = None  # type: tuple # e.g. ('greeting', 'name'), or None to replace all str attributes
    ADDITIONAL_DICT_ATTRS = None  # type: tuple # e.g. ('age', ), or None to add all non-str attributes

    def _format_text(self, text):
        while True:
            old_text = text
            text = format_str_while_preserving_curly_brackets(text, **self._get_formatting_dict())
            if text == old_text:
                return text.format()

    def get_replaced_attributes(self):
        with _do_not_replace(self):
            if self.REPLACED_ATTRS is not None:
                return self.REPLACED_ATTRS
            return [attr for attr in self.__dict__ if isinstance(_super_getatter(self, attr), str)]

    def get_additional_dict_attributes(self):
        with _do_not_replace(self):
            if self.ADDITIONAL_DICT_ATTRS is not None:
                return self.ADDITIONAL_DICT_ATTRS
            return [attr for attr in self.__dict__ if not isinstance(_super_getatter(self, attr), str)
                    and attr != 'is_replacing']

    def _get_formatting_dict(self):
        attributes_for_dict = (*self.get_replaced_attributes(), *self.get_additional_dict_attributes())
        with self.not_replacing_attributes():
            return {attr: getattr(self, attr) for attr in attributes_for_dict}

    def __getattribute__(self, item):
        raw_value = _super_getatter(self, item)
        if _super_get_is_replacing(self) and \
                item in _super_getatter(self, 'get_replaced_attributes')():
            return _super_getatter(self, '_format_text')(raw_value)
        return raw_value

    @contextmanager
    def attributes_replacement(self):
        old_is_replacing = _super_get_is_replacing(self)
        self.is_replacing = True
        try:
            yield
        finally:
            self.is_replacing = old_is_replacing

    @contextmanager
    def not_replacing_attributes(self):
        old_is_replacing = _super_get_is_replacing(self)
        self.is_replacing = False
        try:
            yield
        finally:
            self.is_replacing = old_is_replacing
