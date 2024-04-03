import sys
from enum import Enum
from typing import Optional, List, Collection

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, \
    QSplitter, QTextEdit, QPushButton, QLabel
from PySide6.QtCore import Qt, QEventLoop
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.lexers.python import PythonLexer


class PanelNames(Enum):
    SYSTEM_PROMPT = "System Prompt"
    MISSION_PROMPT = "Mission Prompt"
    PRODUCT = "Product"
    FEEDBACK = "Feedback"


class Panel(QWidget):
    def __init__(self, heading: Optional[str] = None):
        """
        A panel that displays text and allows editing.
        """
        super().__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.heading = heading
        if heading:
            self.heading_label = QLabel(heading)
            self.layout.addWidget(self.heading_label)

    def set_text(self, text):
        pass

    def get_text(self):
        pass


class EditableTextPanel(Panel):
    def __init__(self, heading: Optional[str] = None,
                 suggestion_button_names: Optional[Collection[str]] = None):
        super().__init__(heading)
        if suggestion_button_names is None:
            suggestion_button_names = []
        self.suggestion_button_names = suggestion_button_names
        self.suggestion_buttons = []
        self.suggestion_texts = [''] * len(suggestion_button_names)

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.layout.addWidget(self.text_edit)

        self.buttons_tray = QHBoxLayout()
        self.layout.addLayout(self.buttons_tray)

        self.submit_button = QPushButton("Submit")
        self.submit_button.clicked.connect(self.on_submit)
        self.buttons_tray.addWidget(self.submit_button)

        for i, button_text in enumerate(suggestion_button_names):
            button = QPushButton(button_text)
            button.clicked.connect(self.on_suggestion_button_click)
            self.buttons_tray.addWidget(button)
            self.suggestion_buttons.append(button)
        self._set_buttons_visibility(False)

        self.loop = None
    
    def _set_buttons_visibility(self, visible: bool):
        self.submit_button.setVisible(visible)
        for button in self.suggestion_buttons:
            button.setVisible(visible)

    def on_suggestion_button_click(self):
        button = self.sender()
        suggestion_index = self.suggestion_buttons.index(button)
        self.text_edit.setPlainText(self.suggestion_texts[suggestion_index])

    def set_text(self, text):
        self.text_edit.setReadOnly(True)
        self.text_edit.setPlainText(text)
        self._set_buttons_visibility(False)

    def edit_text(self, text, suggestion_texts: Optional[List[str]] = None):
        self.text_edit.setReadOnly(False)
        self.text_edit.setPlainText(text)
        self._set_buttons_visibility(True)
        if suggestion_texts is not None:
            self.suggestion_texts = suggestion_texts
        self.loop = QEventLoop()
        self.loop.exec()

    def on_submit(self):
        self.text_edit.setReadOnly(True)
        self._set_buttons_visibility(False)
        if self.loop is not None:
            self.loop.exit()

    def get_text(self):
        return self.text_edit.toPlainText()


class HtmlPanel(Panel):
    def __init__(self, heading: Optional[str] = None):
        super().__init__(heading)
        self.text_browser = QTextEdit()
        self.text_browser.setReadOnly(True)
        self.layout.addWidget(self.text_browser)

    def set_text(self, text):
        self.text_browser.setHtml(text)

    def get_text(self):
        return self.text_browser.toPlainText()


class ResearchStepWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.panels = {
            PanelNames.SYSTEM_PROMPT: EditableTextPanel("System Prompt", ("Default", )),
            PanelNames.MISSION_PROMPT: EditableTextPanel("Mission Prompt", ("Default", )),
            PanelNames.PRODUCT: HtmlPanel("Product"),
            PanelNames.FEEDBACK: EditableTextPanel("Feedback", ("AI Review", "No comments")),
        }

        main_splitter = QSplitter(Qt.Horizontal)
        left_splitter = QSplitter(Qt.Vertical)
        right_splitter = QSplitter(Qt.Vertical)

        left_splitter.addWidget(self.panels[PanelNames.SYSTEM_PROMPT])
        left_splitter.addWidget(self.panels[PanelNames.MISSION_PROMPT])
        right_splitter.addWidget(self.panels[PanelNames.PRODUCT])
        right_splitter.addWidget(self.panels[PanelNames.FEEDBACK])

        main_splitter.addWidget(left_splitter)
        main_splitter.addWidget(right_splitter)

        self.setCentralWidget(main_splitter)

    def set_window_title(self, title):
        self.setWindowTitle(title)

    def edit_text_in_panel(self, panel_name: PanelNames, initial_text: str = '', approve_text: Optional[str] = None):
        panel = self.panels[panel_name]
        panel.edit_text(initial_text, suggestion_texts=[initial_text, approve_text])
        return panel.get_text()

    def set_text_in_panel(self, panel_name, text):
        panel = self.panels[panel_name]
        panel.set_text(text)


def get_highlighted_code(sample_code: str, style: str = "monokai") -> str:
    """
    Highlight the provided Python code with the specified style and return the HTML code.
    """
    formatter = HtmlFormatter(style=style)
    css = formatter.get_style_defs('.highlight')
    additional_css = ".highlight, .highlight pre { background: #272822; }  /* Use the monokai background color */"
    highlighted_code = highlight(sample_code, PythonLexer(), formatter)
    return f"<style>{css}{additional_css}</style>{highlighted_code}"


# Boilerplate code to start the application
app = QApplication(sys.argv)
window = ResearchStepWindow()
window.set_window_title("Data Exploration")
window.show()

# Sample Python code to highlight
sample_code = '''
def greet(name):
return f"Hello, {name}!"
'''

# Example usage
code_with_custom_css = get_highlighted_code(sample_code)
window.set_text_in_panel(PanelNames.PRODUCT, code_with_custom_css)
edited_text = window.edit_text_in_panel(PanelNames.FEEDBACK, 'Edit this text...',
                                        'Approved text')
print(edited_text)
window.set_text_in_panel(PanelNames.FEEDBACK, edited_text)

sys.exit(app.exec())
