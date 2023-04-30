from dataclasses import dataclass, field


@dataclass
class Replacer:
    """
    Base class for dataclass classes that have specific str attributes that should be replaced base on the
    values of other attributes.

    name: str = 'john'
    greeting: str = 'hello {name}'
    REPLACED_ATTRS: str = ['greeting']
    ADDITIONAL_DICT_ATTRS: str = ['name']
    """

    is_replacing: bool = False

    REPLACED_ATTRS = []
    ADDITIONAL_DICT_ATTRS = []

    def _format_text(self, text):
        while True:
            old_text = text
            text = text.format(**self._get_formatting_dict())
            if text == old_text:
                return text

    def _get_formatting_dict(self):
        old_is_replacing = self.is_replacing
        self.is_replacing = False
        dict_ = {attr: getattr(self, attr) for attr in self.REPLACED_ATTRS + self.ADDITIONAL_DICT_ATTRS}
        self.is_replacing = old_is_replacing
        return dict_

    def __getattribute__(self, item):
        is_replacing = super().__getattribute__('is_replacing')
        should_replace = item in super().__getattribute__('REPLACED_ATTRS')
        if is_replacing and should_replace:
            return self._format_text(super().__getattribute__(item))
        return super().__getattribute__(item)


