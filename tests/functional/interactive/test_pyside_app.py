import sys
import time

import pytest

from data_to_paper.env import CHOSEN_APP
from data_to_paper.interactive.get_app import get_or_create_q_application_if_app_is_pyside
from data_to_paper.interactive.pyside_app import PysideApp
from data_to_paper.interactive.enum_types import PanelNames
from data_to_paper.text.highlighted_text import format_text_with_code_blocks

long = "This is a very long sentence to test wrapping and proper <b>escaping</b>"
block = f"""
### Title
a, b, c
1, 2, 3
aaaaa 0123
iiiii 0123
{long}
"""

example_test = f"""
This is a regular text.
{long}

We can **bold** and *italicize* text.

It should properly escape html. For example, <b>bold</b> and <i>italic</i> should appear as unformatted html text.

List formatting has been disabled:
Can create a list with '-':
- item 1: {long}
- item 2: {long}

Can create a list with '*':
* item 1: {long}
* item 2: {long}

Should format `print('hi')` as monospace.

`line 1`
`line 2`

`Line 1
Line 2`

and can do two codes `df1` and `df2` in the same line.

This is my code:
```python
print('Hello World!')
# {long}
```

# Header 1
Text under header 1
{long}

## Header 2
Text under header 2
{long}

### Header 3
Text under header 3
{long}

#### Header 4
The space below this line
#### Header 4
Should be the same as the space below this line

#### Header 4
Text under header 4

This is a an OUTPUT code block:
```output
{block}
```

This is a regular block:
```
{block}
```

This is a 'stupid' block:
```stupid
{block}
```

This is a 'md' block:
```md
{block}
```

This is an error code block:
```error
{block}
```

We can also show latex:
```latex
\\title{{This is the title}}
\\abstract{{This is the abstract}}

\\section{{Introduction}}
This is the introduction. It can have citations like this \\cite{{ref1}}.

And equations like this:

\\begin{{equation}}
    E = mc^2
\\end{{equation}}

\\begin{{figure}}[htbp]
\\centering
\\includegraphics[width=0.8]{{average_values.png}}
\\caption{{This is the caption}}
\\label{{this_is_the_label}}
\\end{{figure}}
```
"""

# we can also show an image.
# We have "average_values.png" in the same directory as this file.
html_2 = """
<div>
<img src="average_values.png" alt="This is the caption" width="200" />
</div>
"""


def test_print_html():
    html = format_text_with_code_blocks(example_test, is_html=True, from_md=True, do_not_format=['latex'])
    print(html)


# TODO: Need to make this into a real test
@pytest.mark.skip(reason="Need some work to make it into a real test")
def test_pyside_app():
    def func_to_run():
        # Request text input from the user with an initial text
        app.show_text(PanelNames.MISSION_PROMPT, html_1, is_html=True)
        app.show_text(PanelNames.RESPONSE, html_2, is_html=True)
        text_input = app.request_text(PanelNames.FEEDBACK, 'John', 'write your name:')
        # Simulate a long-running task
        time.sleep(1)
        # Show the processed text in the UI
        app.show_text(PanelNames.SYSTEM_PROMPT, "Hi " + text_input)

    html_1 = format_text_with_code_blocks(example_test, is_html=True, from_md=True, do_not_format=['latex'])
    with CHOSEN_APP.temporary_set('pyside'):
        q_application = get_or_create_q_application_if_app_is_pyside()
        app = PysideApp.get_instance()
        app.initialize(func_to_run)
        sys.exit(q_application.exec())
