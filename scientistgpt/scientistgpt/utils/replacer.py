from dataclasses import dataclass

from scientistgpt.utils.text_extractors import extract_all_external_brackets
from scientistgpt.utils.text_formatting import format_str_by_direct_replace


@dataclass
class Replacer:
    """
    Base class for dataclass classes that have specific str attributes that should be replaced base on the
    values of other attributes.

    name: str = 'john'
    greeting: str = 'hello {name}'
    """

    def _format_text(self, text, should_format: bool = True) -> str:
        if not should_format:
            return text
        brackets = set(extract_all_external_brackets(text, '{'))
        for bracket in brackets:
            bracketed_text = bracket[1:-1]
            if hasattr(self, bracketed_text):
                replace_with = self._format_text(str(getattr(self, bracketed_text)))
                text = text.replace(bracket, replace_with)

        return text
