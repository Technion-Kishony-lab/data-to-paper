import pytest

from data_to_paper.text.text_formatting import forgiving_format


@pytest.mark.parametrize('text, args, kwargs, expected', [
    ('hello, my name is {name}', (), {'name': 'john'}, 'hello, my name is john'),
    ('hello, my name is {}', ('john',), {}, 'hello, my name is john'),
    ('{{hello}}', (), {}, '{hello}'),
    ('{{hello}}', (), {'hello': 'world'}, '{hello}'),
    ('{hello}', (), {'hello': '{world}'}, '{world}'),
    ('{hello} {}', (), {'hello': '{world}'}, '{world} {}'),
    ('{hello} {} {{}}', (), {'hello': '{world}'}, '{world} {} {}'),
])
def test_forgiving_format(text, args, kwargs, expected):
    assert forgiving_format(text, *args, **kwargs) == expected
