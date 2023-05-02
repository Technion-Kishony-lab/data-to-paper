from dataclasses import dataclass

from _pytest.fixtures import fixture

from scientistgpt.utils.replacer import Replacer, with_attribute_replacement


@dataclass
class Greeter(Replacer):
    REPLACED_ATTRS = ['greeting', 'name', 'adjective']
    ADDITIONAL_DICT_ATTRS = ['age']
    age: int = 20
    adjective: str = 'amazing'
    name: str = 'the {adjective} john'
    greeting: str = 'hello, I am {name}, and I am {age} years old. I like {{BRACKETS}}'

    @with_attribute_replacement
    def get_greeting(self):
        return self.greeting


@fixture
def greeter():
    return Greeter()


def test_replacer_has_unformatted_attrs_when_not_replacing(greeter):
    assert greeter.greeting == 'hello, I am {name}, and I am {age} years old. I like {{BRACKETS}}'
    assert greeter.name == 'the {adjective} john'


def test_replacer_has_formatted_attrs_when_replacing(greeter):
    greeter.is_replacing = True
    assert greeter.greeting == 'hello, I am the amazing john, and I am 20 years old. I like {BRACKETS}'
    assert greeter.name == 'the amazing john'


def test_with_attribute_replacement_decorator(greeter):
    assert greeter.get_greeting() == 'hello, I am the amazing john, and I am 20 years old. I like {BRACKETS}'
    assert greeter.greeting == 'hello, I am {name}, and I am {age} years old. I like {{BRACKETS}}'
    assert greeter.name == 'the {adjective} john'
