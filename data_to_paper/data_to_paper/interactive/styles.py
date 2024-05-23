import os

from pygments.formatters.html import HtmlFormatter

ICON_PATH = os.path.join(os.path.dirname(__file__) + '/icons/')

CSS = '''
.runtime_error {
    color: red;
    font-family: Consolas, 'Courier New', monospace; font-size: 14px;
}
.markdown {
    font-family: Arial, sans-serif;
    font-size: 14px;
    color: white;
    overflow-wrap: break-word; /* Allows the words to break and wrap onto the next line */
    word-wrap: break-word; /* Older syntax, similar to overflow-wrap */
    white-space: normal; /* Overrides pre to allow wrapping */
    margin-bottom: 0.5em;
}
.codeline {
    font-family: Consolas, 'Courier New', monospace;
}
h1 {
    color: #0066cc;
    font-size: 18px;
}
h2 {
    color: #0099cc;
    font-size: 16px;
}
h3 {
    color: #00cccc;
    font-size: 14px;
}
li {
    margin-left: 20px;
    padding-left: 0;
    list-style-type: disc;
    margin-bottom: 0.5em;
}
'''

PANEL_HEADER_COLOR = "#0077cc"  # dark blue
CURRENT_STEP_COLOR = '#005599'  # darker blue
SUBMIT_BUTTON_COLOR = '#008000'  # dark green

BACKGROUND_COLOR = "#151515"
APP_BACKGROUND_COLOR = "#303030"

formatter = HtmlFormatter(style="monokai")
css = formatter.get_style_defs('.highlight')
additional_css = ".highlight, .highlight pre { background: " + BACKGROUND_COLOR + "; }"

# combine the CSS with the additional CSS:
CSS += css + additional_css

# SCROLLBAR_STYLE = """
# QScrollBar:horizontal {
#     border: none;
#     background: #f0f0f0;
#     height: 12px;
#     margin: 0px 0px 0px 0px;
#     border-radius: 6px;
# }
#
# QScrollBar::handle:horizontal {
#     background: #a0a0a0;
#     min-width: 20px;
#     border-radius: 6px;
# }
#
# QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
#     border: none;
#     background: none;
#     width: 0px;
#     height: 0px;
# }
#
# QScrollBar:vertical {
#     border: none;
#     background: #f0f0f0;
#     width: 12px;
#     margin: 0px 0px 0px 0px;
#     border-radius: 6px;
# }
#
# QScrollBar::handle:vertical {
#     background: #a0a0a0;
#     min-height: 20px;
#     border-radius: 6px;
# }
#
# QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
#     border: none;
#     background: none;
#     width: 0px;
#     height: 0px;
# }
#
# QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical,
# QScrollBar::left-arrow:horizontal, QScrollBar::right-arrow:horizontal {
#     background: none;
#     border: none;
# }
#
# QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical,
# QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
#     background: none;
# }
# """

SCROLLBAR_STYLE = """
QScrollBar:horizontal {
    border: none;
    background: transparent; /* Remove background color */
    height: 8px; /* Make the scrollbar smaller */
    margin: 0px 0px 0px 0px;
    border-radius: 4px; /* Adjust border-radius to match new size */
}

QScrollBar::handle:horizontal {
    background: #a0a0a0;
    min-width: 20px;
    border-radius: 4px; /* Adjust border-radius to match new size */
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    border: none;
    background: transparent;
    width: 0px;
    height: 0px;
}

QScrollBar:vertical {
    border: none;
    background: transparent; /* Remove background color */
    width: 8px; /* Make the scrollbar smaller */
    margin: 0px 0px 0px 0px;
    border-radius: 4px; /* Adjust border-radius to match new size */
}

QScrollBar::handle:vertical {
    background: #a0a0a0;
    min-height: 20px;
    border-radius: 4px; /* Adjust border-radius to match new size */
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: transparent;
    width: 0px;
    height: 0px;
}

QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical,
QScrollBar::left-arrow:horizontal, QScrollBar::right-arrow:horizontal {
    background: none;
    border: none;
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical,
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: none;
}
"""

APP_STYLE = """
QMainWindow {
   background-color: black;
}
""".replace('black', APP_BACKGROUND_COLOR) + SCROLLBAR_STYLE

TABS_STYLE = """
QTabWidget::pane { /* The tab widget frame */
    border-top: 2px solid #202020;
}

QTabBar::tab {
    background-color: #303030;
    color: white;
    border: 2px solid #505050; /* Visible borders around tabs */
    border-bottom-color: #303030; /* Same as background to merge with the tab pane */
    padding: 5px; /* Spacing within the tabs */
}

QTabBar::tab:selected {
    background-color: #505050;
    border-color: #606060; /* Slightly lighter border to highlight the selected tab */
    border-bottom-color: #505050; /* Merge with the tab pane */
}

QTabBar::tab:hover {
    background-color: #404040; /* Slightly lighter to indicate hover state */
}
"""


QEDIT_STYLE = """
QTextEdit {
    color: red;  /* Color for the actual text */
    background-color: """ + BACKGROUND_COLOR + """;
    font-size: 14px;
}
"""

HTMLPOPUP_STYLE = """
* {
    background-color: """ + BACKGROUND_COLOR + """;
}
QPushButton {
    background-color: #E3E0DA; 
    color: """ + BACKGROUND_COLOR + """;
}
""" + SCROLLBAR_STYLE

STEP_PANEL_BUTTON_STYLE = """
QPushButton {{
    background-color: {background_color};
    border-radius: 5px;
}}
QPushButton:pressed {{
    background-color: {pressed_color};
}}
"""

MAIN_SPLITTER_STYLE = """
QSplitter::handle {
    width: 1px;
    background-color: #202020;
    }
"""

QCHECKBOX_STYLE = """
QCheckBox {
    color: rgb(255,255,255); /* Text color */
}

QCheckBox::indicator {
    width: 15px;
    height: 15px;
}

QCheckBox::indicator:unchecked {
    border: 1px solid white;
}

QCheckBox::indicator:checked {
    border: 1px solid white;
    image: url(""" + ICON_PATH + """checkmark.png);
}
"""
