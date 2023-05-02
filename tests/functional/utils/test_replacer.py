from dataclasses import dataclass

from scientistgpt.utils.replacer import Replacer


@dataclass
class Greeter(Replacer):
    REPLACED_ATTRS = ['greeting', 'name', 'adjective']
    ADDITIONAL_DICT_ATTRS = ['age']
    age: int = 20
    adjective: str = 'amazing'
    name: str = 'the {adjective} john'
    greeting: str = 'hello, I am {name}, and I am {age} years old'


def test_replacer():
    greeter = Greeter()

    assert greeter.greeting == 'hello, I am {name}, and I am {age} years old'

    greeter.is_replacing = True
    assert greeter.greeting == 'hello, I am the amazing john, and I am 20 years old'

    greeter.is_replacing = False
    assert greeter.greeting == 'hello, I am {name}, and I am {age} years old'
    assert greeter.name == 'the {adjective} john'
