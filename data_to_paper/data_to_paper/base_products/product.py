from dataclasses import dataclass
from typing import Any

from data_to_paper.code_and_output_files.file_view_params import ContentViewPurpose
from data_to_paper.conversation.stage import Stage
from data_to_paper.utils import format_text_with_code_blocks
from data_to_paper.utils.text_formatting import wrap_text_with_triple_quotes


@dataclass
class Product:
    """
    A product is a piece of information that is generated during the conversation.
    A product needs to know how to be presented:
    - as markdown, to be included in a pre-conversation context.
    - as html, to be be shown in the app.
    """
    name: str = None
    stage: Stage = None
    pre_text_for_markdown: str = None
    pre_text_for_html: str = None
    show_markdown_with_code_blocks: bool = True

    def _get_pre_text_for_markdown(self, level: int, **kwargs) -> str:
        return self.pre_text_for_markdown or ''

    def _get_pre_text_for_html(self, level: int, **kwargs) -> str:
        return self.pre_text_for_html if self.pre_text_for_html is not None \
            else self.pre_text_for_markdown

    def get_stage(self, **kwargs) -> Stage:
        return self.stage

    def is_valid(self):
        raise NotImplementedError

    def _get_content_as_markdown(self, level: int, **kwargs) -> str:
        return ''

    def _get_content_as_html(self, level: int, **kwargs) -> str:
        return format_text_with_code_blocks(self._get_content_as_markdown(level, **kwargs), from_md=True,
                                            is_html=True, width=None)

    def get_header(self, **kwargs) -> str:
        return self.name

    def as_markdown(self, level: int = 1, **kwargs) -> str:
        """
        Return the product in the form to be included in a pre-conversation context.
        Typically, this is a markdown format.
        """
        content = self._get_content_as_markdown(level, **kwargs)
        if self.show_markdown_with_code_blocks:
            return wrap_text_with_triple_quotes(content, 'markdown')
        return ('#' * level + ' ' + self.get_header(**kwargs) + '\n' +
                self._get_pre_text_for_markdown(level, **kwargs) +
                content)

    def as_html(self, level: int = 0, **kwargs):
        return f'<h{level}>{self.get_header(**kwargs)}</h{level}>' + self._get_content_as_html(level, **kwargs)


@dataclass
class ValueProduct(Product):
    value: Any = None

    def is_valid(self):
        return self.value is not None

    def _get_content_as_markdown(self, level: int, **kwargs):
        return str(self.value)

    def __getitem__(self, item):
        return self.value[item]

    def __setitem__(self, key, value):
        self.value[key] = value

    def __iter__(self):
        return iter(self.value)

    def items(self):
        return self.value.items()

    def keys(self):
        return self.value.keys()

    def values(self):
        return self.value.values()

    def __len__(self):
        return len(self.value)

    def __contains__(self, item):
        return item in self.value
