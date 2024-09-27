import pytest

from data_to_paper.text.formatted_sections import FormattedSections


@pytest.mark.parametrize('text, labels, is_complete', [
    ("```single line block```", ('', ), True),
    ('hello', (None, ), True),
    ("```python\na = 2\n```", ('python', ), True),
    ("```\na = 2\n```", ('', ), True),
    ("```\na = 2\n", ('', ), False),
    ("Here is our code:\n```python\n\nimport numpy as np\n```", (None, 'python', ), True),
])
def test_formatted_sections_converts_back_perfectly(text, labels, is_complete):
    formatted_sections = FormattedSections.from_text(text, strip_label=False)
    assert tuple(fs.label for fs in formatted_sections) == labels
    assert formatted_sections.is_last_block_incomplete() == (not is_complete)
    assert formatted_sections.to_text() == text


def test_formatted_sections_strip_labels():
    formatted_sections = FormattedSections.from_text("``` python \na = 2\n```", strip_label=True)
    assert formatted_sections[0].label == 'python'
    assert formatted_sections.to_text() == "```python\na = 2\n```"


def test_empty_formatted_sections():
    formatted_sections = FormattedSections.from_text('')
    assert formatted_sections.to_text() == ''
    assert not formatted_sections.is_last_block_incomplete()
    assert len(formatted_sections) == 0
