from dataclasses import dataclass, field
from typing import Tuple, Union, Any

from scientistgpt.utils.text_extractors import extract_all_external_brackets
from scientistgpt.utils.text_formatting import forgiving_format


@dataclass
class Replacer:
    obj: Any = None
    text: str = ''
    args: Tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)

    def __str__(self):
        return self.format_text()

    def format_text(self) -> str:
        text = self.text
        brackets = set(extract_all_external_brackets(self.text, '{'))
        additional_kwargs = {}
        for bracket in brackets:
            bracketed_text = bracket[1:-1]
            if hasattr(self.obj, bracketed_text):
                attr = getattr(self.obj, bracketed_text)
                if not isinstance(attr, Replacer):
                    attr = Replacer(self.obj, str(attr))
                attr = attr.format_text()
                additional_kwargs[bracketed_text] = attr

        return forgiving_format(text, *self.args, **self.kwargs, **additional_kwargs)


def format_value(obj, value: Any, should_format: bool = True) -> Union[str, Any]:
    if not should_format:
        return value
    if isinstance(value, Replacer):
        return value.format_text()
    elif isinstance(value, str):
        return Replacer(obj, value).format_text()
    else:
        return value


StrOrTextFormat = Union[str, Replacer]
