from dataclasses import dataclass

from scientistgpt.utils.replacer import Replacer


@dataclass
class Greeter(Replacer):
    REPLACED_ATTRS = ['greeting', 'name']
    ADDITIONAL_DICT_ATTRS = ['name', 'adjective']
    adjective = 'amazing'
    name: str = 'the {adjective} john'
    greeting: str = 'hello {name}'


def test_replacer():
    greeter = Greeter()

    assert greeter.greeting == 'hello {name}'

    greeter.is_replacing = True
    assert greeter.greeting == 'hello the amazing john'

    greeter.is_replacing = False
    assert greeter.greeting == 'hello {name}'
    assert greeter.name == 'the {adjective} john'
