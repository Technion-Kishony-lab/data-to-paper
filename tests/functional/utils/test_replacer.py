from dataclasses import dataclass
from pytest import fixture

from data_to_paper.utils.replacer import format_value, Replacer


@dataclass
class Greeter:
    age: int = 20
    adjective: str = 'amazing'
    name: str = 'the {adjective} john'
    inline_formatted_name: str = 'the {} joe'
    greeting: str = 'hello, I am {name}, and I am {age} years old. I like {BRACKETS}'
    inline_formatted_greeting: str = 'hello, I am {inline_formatted_name}.'


@fixture
def greeter():
    return Greeter()


def test_replacer(greeter):
    assert format_value(greeter, greeter.greeting) == \
           'hello, I am the amazing john, and I am 20 years old. I like {BRACKETS}'


def test_replacer_with_inline_formatting(greeter):
    greeter.inline_formatted_name = Replacer(greeter, 'the {} joe', args=('lousy',))
    assert format_value(greeter, greeter.inline_formatted_greeting) == \
           'hello, I am the lousy joe.'
