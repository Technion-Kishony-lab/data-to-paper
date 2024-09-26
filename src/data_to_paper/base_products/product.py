from dataclasses import dataclass
from typing import Any

from data_to_paper.code_and_output_files.file_view_params import ViewPurpose
from data_to_paper.conversation.stage import Stage
from data_to_paper.text.highlighted_text import format_text_with_code_blocks


@dataclass
class Product:
    """
    A product is a piece of information that is generated during the conversation.
    A product needs to know how to be presented:
    - as markdown, to be included in a pre-conversation context.
    - as html, to be shown in the app.
    """
    name: str = None
    stage: Stage = None

    def get_stage(self, **kwargs) -> Stage:
        return self.stage

    def is_valid(self):
        raise NotImplementedError

    def _get_content_as_formatted_text(self, level: int, view_purpose: ViewPurpose, **kwargs) -> str:
        raise NotImplementedError

    def _get_content_as_html(self, level: int, **kwargs) -> str:
        return format_text_with_code_blocks(self._get_content_as_formatted_text(level, ViewPurpose.APP_HTML, **kwargs),
                                            from_md=True, is_html=True, width=None)

    def get_header(self, view_purpose: ViewPurpose = ViewPurpose.PRODUCT, **kwargs) -> str:
        return self.name

    def as_formatted_text(self, level: int = 1, with_header: bool = True,
                          view_purpose: ViewPurpose = ViewPurpose.PRODUCT,
                          **kwargs) -> str:
        """
        Return the product in the form to be included in a pre-conversation context.
        Typically, this is a markdown format.
        """
        s = ''
        if with_header:
            s += '#' * level + ' ' + self.get_header(**kwargs) + '\n'
        s += self._get_content_as_formatted_text(level, view_purpose=view_purpose, **kwargs)
        return s

    def as_html(self, level: int = 0, with_header: bool = True, **kwargs) -> str:
        s = ''
        if with_header:
            s += f'<h{level}>{self.get_header(**kwargs)}</h{level}>'
        s += self._get_content_as_html(level, **kwargs)
        return s


@dataclass
class ValueProduct(Product):
    value: Any = None

    def is_valid(self):
        return self.value is not None

    def _get_content_as_formatted_text(self, level: int, view_purpose: ViewPurpose, **kwargs) -> str:
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
