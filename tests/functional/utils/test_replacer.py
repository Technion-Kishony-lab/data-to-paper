from dataclasses import dataclass

import pytest
from _pytest.fixtures import fixture


@dataclass
class Greeter(Replacer):
    REPLACED_ATTRS = {'greeting', 'name', 'adjective', 'age'}
    age: int = 20
    adjective: str = 'amazing'
    name: str = 'the {adjective} john'
    greeting: str = 'hello, I am {name}, and I am {age} years old. I like {BRACKETS}'

    def get_greeting(self):
        return self.greeting


@dataclass
class AutoGreeter(Greeter):
    REPLACED_ATTRS = None


@fixture
def greeter():
    return Greeter()


@fixture
def auto_greeter():
    return AutoGreeter()


@pytest.mark.parametrize('is_replacing', [True, False])
def test_replacer_automatic_replacement(auto_greeter, is_replacing):
    auto_greeter._is_replacing = is_replacing
    assert auto_greeter.REPLACED_ATTRS is None, 'sanity'
    assert set(auto_greeter.get_replaced_attributes()) == {'greeting', 'name', 'adjective', 'age'}


def test_replacer_has_unformatted_attrs_when_not_replacing(greeter):
    assert greeter.greeting == 'hello, I am {name}, and I am {age} years old. I like {BRACKETS}'
    assert greeter.name == 'the {adjective} john'


def test_replacer_has_formatted_attrs_when_replacing(greeter):
    with greeter.attributes_replacement():
        assert greeter.greeting == 'hello, I am the amazing john, and I am 20 years old. I like {BRACKETS}'
        assert greeter.name == 'the amazing john'


def test_with_attribute_replacement_decorator(greeter):
    assert greeter.get_greeting() == 'hello, I am the amazing john, and I am 20 years old. I like {BRACKETS}'
    assert greeter.greeting == 'hello, I am {name}, and I am {age} years old. I like {BRACKETS}'
    assert greeter.name == 'the {adjective} john'
