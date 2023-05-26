from dataclasses import dataclass
from _pytest.fixtures import fixture

from scientistgpt.utils.replacer import Replacer, TextFormat


@dataclass
class Greeter(Replacer):
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
    assert greeter.format_text(greeter.greeting) == \
           'hello, I am the amazing john, and I am 20 years old. I like {BRACKETS}'


def test_replacer_with_inline_formatting(greeter):
    assert greeter.format_text(TextFormat(greeter.inline_formatted_greeting, args=('lousy',))) == \
           'hello, I am the lousy joe.'
