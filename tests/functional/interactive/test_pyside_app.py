import sys
import time

import pytest

from data_to_paper.env import CHOSEN_APP
from data_to_paper.interactive.get_app import get_or_create_q_application_if_app_is_pyside
from data_to_paper.interactive.pyside_app import PysideApp
from data_to_paper.interactive.enum_types import PanelNames
from data_to_paper.utils.highlighted_text import format_text_with_code_blocks

long = "This is a very long sentence to test wrapping in different formats"

example_test = f"""
This is a regular text with a code block:
{long}

We can **bold** and *italicize* text.

It should properly escape html. For example, <b>bold</b> and <i>italic</i> should appear as unformatted html text.

Can create a list with '-':
- item 1: {long}
- item 2: {long}

Can create a list with '*':
* item 1: {long}
* item 2: {long}

```python
print('Hello World!')
# {long}
```

# Header 1
Test under header 1
{long}

## Header 2
Test under header 2
{long}

### Header 3
Test under header 3
{long}

#### Header 4
The space below this line
#### Header 4
Should be the same as the space below this line

#### Header 4
Test under header 4

This is a an OUTPUT code block:
```output
a, b, c
1, 2, 3
aaaaa 0123
iiiii 0123
{long}
```

This is a regular block:
```
aaaaa 0123
iiiii 0123
Text inside a regular block
```

This is an error code block:
```error
aaaaa 0123
iiiii 0123
{long}
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
```

"""

html = format_text_with_code_blocks(example_test, is_html=True, from_md=True)


# TODO: Need to make this into a real test
@pytest.mark.skip(reason="Need some work to make it into a real test")
def test_pyside_app():
    def func_to_run():
        # Request text input from the user with an initial text
        app.show_text(PanelNames.MISSION_PROMPT, html, is_html=True)
        text_input = app.request_text(PanelNames.FEEDBACK, 'John', 'write your name:')
        # Simulate a long-running task
        time.sleep(1)
        # Show the processed text in the UI
        app.show_text(PanelNames.SYSTEM_PROMPT, "Hi " + text_input)

    with CHOSEN_APP.temporary_set('pyside'):
        q_application = get_or_create_q_application_if_app_is_pyside()
        app = PysideApp.get_instance()
        app.initialize(func_to_run)
        sys.exit(q_application.exec())
