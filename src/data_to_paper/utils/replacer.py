from dataclasses import dataclass, field
from typing import Tuple, Union, Any, Optional

from data_to_paper.text.text_extractors import extract_all_external_brackets
from data_to_paper.text.text_formatting import forgiving_format
from data_to_paper.utils.types import ListBasedSet


@dataclass
class Replacer:
    """
    A class to replace placeholders in a string with the attributes of a given object (or of multiple objects).
    Also allows adding additional args and kwargs for the string formatting.
    Formatting is done by calling forgiving_format(), so matching placeholders are replaced and non-matching
    are left as is.
    """
    objs: Optional[Union[Any, list]] = None
    text: str = ''
    args: Tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)

    def __str__(self):
        return self.format_text()

    def __bool__(self):
        return bool(self.text)

    def add_obj(self, obj):
        if self.objs is None:
            self.objs = obj
        elif not isinstance(self.objs, list):
            self.objs = [self.objs] + [obj]
        else:
            self.objs.append(obj)

    def get_objs(self):
        if self.objs is None:
            return []
        elif isinstance(self.objs, list):
            return self.objs
        else:
            return [self.objs]

    def format_text(self) -> str:
        text = self.text
        brackets = ListBasedSet(extract_all_external_brackets(self.text, '{'))
        additional_kwargs = {}
        objs = self.get_objs()
        for bracket in brackets:
            bracketed_text = bracket[1:-1]
            for obj in objs:
                if hasattr(obj, bracketed_text):
                    attr = getattr(obj, bracketed_text)
                    if not isinstance(attr, Replacer):
                        attr = Replacer(obj, str(attr))
                    attr = attr.format_text()
                    additional_kwargs[bracketed_text] = attr
                    break
            else:
                pass  # we don't have the attribute in any of the objects, so we don't do anything
        # add object kwargs:
        for obj in objs:
            if hasattr(obj, 'replacer_kwargs'):
                additional_kwargs.update(obj.replacer_kwargs)

        return forgiving_format(text, *self.args, **self.kwargs, **additional_kwargs)


def format_value(obj: object, value: Any, should_format: bool = True) -> Union[str, Any]:
    if not should_format:
        return value
    if isinstance(value, Replacer):
        value.add_obj(obj)
        return value.format_text()
    elif isinstance(value, str):
        return Replacer(obj, value).format_text()
    else:
        return value


StrOrReplacer = Union[str, Replacer]
