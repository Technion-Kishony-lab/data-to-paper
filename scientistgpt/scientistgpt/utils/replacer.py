from dataclasses import dataclass
from typing import Tuple, Union

from scientistgpt.utils.text_extractors import extract_all_external_brackets
from scientistgpt.utils.text_formatting import ArgsOrKwargs, format_with_args_or_kwargs

StringFormat = Union[str, Tuple[str, ArgsOrKwargs]]


@dataclass
class Replacer:
    """
    Base class for dataclass classes that have specific str attributes that should be replaced base on the
    values of other attributes.
    for example:
    name: str = 'john'
    greeting: str = 'hello {name}'
    """

    def format_text(self, text: StringFormat, should_format: bool = True) -> str:
        if isinstance(text, tuple):
            text, args_or_kwargs = text
        else:
            args_or_kwargs = None
        if should_format:
            brackets = set(extract_all_external_brackets(text, '{'))
            for bracket in brackets:
                bracketed_text = bracket[1:-1]
                if hasattr(self, bracketed_text):
                    replace_with = self.format_text(str(getattr(self, bracketed_text)))
                    text = text.replace(bracket, replace_with)

        if args_or_kwargs is None:
            return text
        return format_with_args_or_kwargs(text, args_or_kwargs)
