import re

from contextlib import contextmanager
from dataclasses import dataclass, fields


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
    return _super_getatter(self, '_is_replacing')


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
    REPLACED_ATTRS: tuple = ('greeting', )
    ADDITIONAL_DICT_ATTRS: tuple = ('name', )
    """

    _is_replacing = False

    REPLACED_ATTRS = None  # type: tuple # e.g. ('greeting', 'name'), or None to replace all str attributes
    ADDITIONAL_DICT_ATTRS = None  # type: tuple # e.g. ('age', ), or None to add all non-str attributes

    def _format_text(self, text):
        while True:
            old_text = text
            text = format_str_while_preserving_curly_brackets(text, **self._get_formatting_dict())
            if text == old_text:
                return text.format()

    @classmethod
    def get_replaced_attributes(cls):
        if cls.REPLACED_ATTRS is not None:
            return cls.REPLACED_ATTRS
        return tuple(attr.name for attr in fields(cls) if not attr.name.startswith('_'))

    def _get_formatting_dict(self):
        with self.not_replacing_attributes():
            return {attr: getattr(self, attr) for attr in self.get_replaced_attributes() +
                    (self.ADDITIONAL_DICT_ATTRS or ())}

    def __getattribute__(self, item):
        raw_value = _super_getatter(self, item)
        if isinstance(raw_value, str) and _super_get_is_replacing(self) and \
                item in type(self).get_replaced_attributes():
            return _super_getatter(self, '_format_text')(raw_value)
        return raw_value

    @contextmanager
    def attributes_replacement(self):
        old_is_replacing = _super_get_is_replacing(self)
        self._is_replacing = True
        try:
            yield
        finally:
            self._is_replacing = old_is_replacing

    @contextmanager
    def not_replacing_attributes(self):
        old_is_replacing = _super_get_is_replacing(self)
        self._is_replacing = False
        try:
            yield
        finally:
            self._is_replacing = old_is_replacing

    def set(self, **kwargs):
        """
        Set attributes of the class.
        """
        for key, value in kwargs.items():
            setattr(self, key, value)
        return self
