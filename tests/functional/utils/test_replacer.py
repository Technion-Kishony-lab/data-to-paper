from dataclasses import dataclass
from _pytest.fixtures import fixture

from scientistgpt.utils.replacer import Replacer


@dataclass
class Greeter(Replacer):
    age: int = 20
    adjective: str = 'amazing'
    name: str = 'the {adjective} john'
    greeting: str = 'hello, I am {name}, and I am {age} years old. I like {BRACKETS}'

    def get_greeting(self):
        return self._format_text(self.greeting)


@fixture
def greeter():
    return Greeter()


def test_replacer(greeter):
    assert greeter.get_greeting() == 'hello, I am the amazing john, and I am 20 years old. I like {BRACKETS}'
