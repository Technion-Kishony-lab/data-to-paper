from dataclasses import dataclass
from typing import Any

from data_to_paper.utils import format_text_with_code_blocks
from data_to_paper.utils.text_formatting import wrap_text_with_triple_quotes


@dataclass
class Product:
    name: str = None

    def _is_valid(self):
        raise NotImplementedError

    def _get_content_as_text(self, level: int, **kwargs):
        return ''

    def _get_content_as_markdown(self, level: int, **kwargs):
        return self._get_content_as_text(level, **kwargs)

    def _get_content_as_html(self, level: int, **kwargs):
        return format_text_with_code_blocks(self._get_content_as_markdown(level, **kwargs), from_md=True,
                                            is_html=True, width=None)

    def as_text(self, level: int = 0, **kwargs):
        return self.name + '\n' + self._get_content_as_text(level)

    def as_markdown(self, level: int = 0, **kwargs):
        return ('#' * level + ' ' + self.name + '\n' +
                wrap_text_with_triple_quotes(self._get_content_as_markdown(level), 'md'))

    def as_html(self, level: int = 0, **kwargs):
        return f'<h{level}>{self.name}</h{level}>' + self._get_content_as_html(level, **kwargs)

    def as_specified_format(self, format_name, level: int = 0):
        return getattr(self, f'as_{format_name}')(level)

    def to_extracted_test(self):
        raise NotImplementedError

    @classmethod
    def from_extracted_test(cls, text):
        raise NotImplementedError


@dataclass
class SingleValueProduct(Product):
    value: Any = None

    def _is_valid(self):
        return self.value is not None

    def _get_content_as_text(self, level: int, **kwargs):
        return str(self.value)

    def to_extracted_test(self):
        return self.value

    @classmethod
    def from_extracted_test(cls, text):
        return cls(value=text)

    def __getitem__(self, item):
        return self.value[item]

    def __setitem__(self, key, value):
        self.value[key] = value

    def __iter__(self):
        return iter(self.value)
