from contextlib import contextmanager
from dataclasses import dataclass, fields
from typing import Set

from scientistgpt.utils.text_formatting import format_str_by_direct_replace


@dataclass
class Replacer:
    """
    Base class for dataclass classes that have specific str attributes that should be replaced base on the
    values of other attributes.

    name: str = 'john'
    greeting: str = 'hello {name}'
    REPLACED_ATTRS: set = {'greeting'}
    ADDITIONAL_DICT_ATTRS: set = {'name'}
    """

    def _format_text(self, text):
        while True:
            old_text = text
            text = format_str_by_direct_replace(text, self._get_formatting_dict())
            if text == old_text:
                return text

