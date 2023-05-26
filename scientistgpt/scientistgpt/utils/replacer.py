from dataclasses import dataclass, field
from typing import Tuple, Union, Any

from scientistgpt.utils.text_extractors import extract_all_external_brackets


@dataclass
class TextFormat:
    text: str
    args: Tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)

    def __str__(self):
        return self.text.format(*self.args, **self.kwargs)


StrOrTextFormat = Union[str, TextFormat]


@dataclass
class Replacer:
    """
    Base class for dataclass classes that have specific str attributes that should be replaced base on the
    values of other attributes.
    for example:
    name: str = 'john'
    greeting: str = 'hello {name}'
    """

    def format_text(self, str_or_text_format: Union[StrOrTextFormat, Any], should_format: bool = True,
                    is_first: bool = True) -> Union[str, Any]:
        if is_first and not isinstance(str_or_text_format, (TextFormat, str)):
            return str_or_text_format
        if isinstance(str_or_text_format, TextFormat):
            text = str_or_text_format.text
        else:
            text = str_or_text_format

        if not isinstance(text, str):
            return str(text)

        if should_format:
            brackets = set(extract_all_external_brackets(text, '{'))
            for bracket in brackets:
                bracketed_text = bracket[1:-1]
                if hasattr(self, bracketed_text):
                    replace_with = self.format_text(str(getattr(self, bracketed_text)), is_first=False)
                    text = text.replace(bracket, replace_with)

        if isinstance(str_or_text_format, TextFormat):
            str_or_text_format.text = text
            return str(str_or_text_format)
        else:
            return text

    def set(self, **kwargs):
        """
        Set attributes of the class.
        """
        for key, value in kwargs.items():
            setattr(self, key, value)
        return self
