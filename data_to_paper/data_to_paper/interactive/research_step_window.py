from functools import partial
from typing import Optional, List, Collection, Dict, Callable

from PySide6.QtGui import QTextOption
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QLabel, QPushButton, QWidget, \
    QHBoxLayout, QSplitter, QTextEdit, QTabWidget
from PySide6.QtCore import Qt, QEventLoop, QMutex, QWaitCondition, QThread, Signal, Slot

from pygments.formatters.html import HtmlFormatter
from pygments.lexers.python import PythonLexer

from data_to_paper.interactive.base_app import BaseApp
from data_to_paper.interactive.types import PanelNames

# orange color: #FFA500
# slightly darker orange: #FF8C00

CSS = '''
.text_highlight, .text_highlight span {
    color: #FFA500;
}
.textblock_highlight {
    font-family: Consolas, 'Courier New', monospace; font-weight: bold;
    color: #FF8C00;
}
'''

formatter = HtmlFormatter(style="monokai")
css = formatter.get_style_defs('.highlight')
additional_css = ".highlight, .highlight pre { background: #272822; }  /* Use the monokai background color */"

# combine the CSS with the additional CSS:
CSS += css + additional_css

class Worker(QThread):
    # Signal now carries a string payload for initial text
    request_input_signal = Signal(PanelNames, str, str, dict)
    show_text_signal = Signal(PanelNames, str, bool)

    def __init__(self, mutex, condition, func_to_run=None):
        super().__init__()
        self.mutex = mutex
        self.condition = condition
        self.func_to_run = func_to_run
        self._text_input = None
        self._panel_name_input = None

    def run(self):
        if self.func_to_run is not None:
            self.func_to_run()

    def edit_text_in_panel(self, panel_name: PanelNames, initial_text: str = '',
                           title: Optional[str] = None, optional_suggestions: Dict[str, str] = None) -> str:
        self.mutex.lock()
        self.request_input_signal.emit(panel_name, initial_text, title, optional_suggestions)
        self.condition.wait(self.mutex)
        input_text = self._text_input
        self.mutex.unlock()
        return input_text

    def show_text_in_panel(self, panel_name: PanelNames, text: str, is_html: bool = False):
        self.show_text_signal.emit(panel_name, text, is_html)

    @Slot(PanelNames, str)
    def set_text_input(self, panel_name, text):
        self.mutex.lock()
        self._text_input = text
        self._panel_name_input = panel_name
        self.condition.wakeAll()
        self.mutex.unlock()


class Panel(QWidget):
    def __init__(self, header: Optional[str] = None):
        """
        A panel that displays text and allows editing.
        """
        super().__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.header = header
        self.header_label = QLabel(header)
        # nice light blue color (customized)
        self.header_label.setStyleSheet("color: #0077cc; font-size: 16px; font-weight: bold;")
        self.layout.addWidget(self.header_label)

    def reset_instructions(self):
        if self.instructions is not None:
            self.instructions_label.setText(self.instructions)

    def set_text(self, text):
        pass

    def get_text(self):
        pass


class EditableTextPanel(Panel):
    def __init__(self, header: str,
                 suggestion_button_names: Optional[Collection[str]] = None):
        super().__init__(header)
        if suggestion_button_names is None:
            suggestion_button_names = []
        self.suggestion_button_names = suggestion_button_names
        self.suggestion_buttons = []
        self.suggestion_texts = [''] * len(suggestion_button_names)

        self.text_edit = QTextEdit()
        self.text_edit.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        self.text_edit.setFontPointSize(18)

        self.text_edit.setReadOnly(True)
        self.layout.addWidget(self.text_edit)

        # Instructions:
        self.instructions = None
        self.instructions_label = QLabel()
        self.reset_instructions()
        self.layout.addWidget(self.instructions_label)

        # Buttons:
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
        self.instructions_label.setVisible(visible)
        for button in self.suggestion_buttons:
            button.setVisible(visible)

    def reset_instructions(self):
        if self.instructions is not None:
            self.instructions_label.setText(self.instructions)

    def on_suggestion_button_click(self):
        button = self.sender()
        suggestion_index = self.suggestion_buttons.index(button)
        if suggestion_index < len(self.suggestion_texts):
            self.text_edit.setPlainText(self.suggestion_texts[suggestion_index])

    def _set_plain_text(self, text: str):
        self.text_edit.setPlainText(text)
        self.text_edit.setStyleSheet("color: orange;")

    def _set_html_text(self, text: str):
        # add the CSS to the HTML
        self.text_edit.setHtml(f'<style>{CSS}</style>{text}')
        self.text_edit.setStyleSheet("color: white;")

    def set_text(self, text: str, is_html: bool = False):
        self.text_edit.setReadOnly(True)
        if is_html:
            self._set_html_text(text)
        else:
            self._set_plain_text(text)
        self._set_buttons_visibility(False)

    def edit_text(self, text: Optional[str] = '', title: Optional[str] = None,
                  suggestion_texts: Optional[List[str]] = None):
        self.text_edit.setReadOnly(False)
        self._set_plain_text(text)
        self._set_buttons_visibility(True)
        if suggestion_texts is not None:
            self.suggestion_texts = suggestion_texts
        title = title or ''
        self.instructions_label.setText(title)
        self.loop = QEventLoop()
        self.loop.exec()

    def on_submit(self):
        self.text_edit.setReadOnly(True)
        self._set_buttons_visibility(False)
        self.reset_instructions()
        if self.loop is not None:
            self.loop.exit()

    def get_text(self):
        return self.text_edit.toPlainText()


def create_tabs(names_to_panels: Dict[str, Panel]):
    tabs = QTabWidget()
    for panel_name, panel in names_to_panels.items():
        tabs.addTab(panel, panel_name)
    return tabs


class ResearchStepApp(QMainWindow, BaseApp):
    send_text_signal = Signal(str, PanelNames)

    def __init__(self, mutex, condition):
        super().__init__()
        self.panels = {
            PanelNames.SYSTEM_PROMPT: EditableTextPanel("System Prompt", ("Default", )),
            PanelNames.MISSION_PROMPT: EditableTextPanel("Mission Prompt", ("Default", )),
            PanelNames.RESPONSE: EditableTextPanel("Response"),
            PanelNames.PRODUCT: EditableTextPanel("Product"),
            PanelNames.FEEDBACK: EditableTextPanel("Feedback", ("AI Review", "No comments")),
        }
        central_widget = QWidget()
        self.layout = QVBoxLayout(central_widget)
        self.layout.addWidget(QLabel("Current step:"))

        main_splitter = QSplitter(Qt.Horizontal)
        left_splitter = QSplitter(Qt.Vertical)
        left_splitter.setHandleWidth(5)
        right_splitter = QSplitter(Qt.Vertical)

        left_splitter.addWidget(self.panels[PanelNames.SYSTEM_PROMPT])
        left_splitter.addWidget(self.panels[PanelNames.MISSION_PROMPT])
        right_splitter.addWidget(create_tabs({'Response': self.panels[PanelNames.RESPONSE],
                                              'Product': self.panels[PanelNames.PRODUCT]}))
        right_splitter.addWidget(self.panels[PanelNames.FEEDBACK])

        main_splitter.addWidget(left_splitter)
        main_splitter.addWidget(right_splitter)

        left_splitter.setSizes([100, 400])
        self.layout.addWidget(main_splitter)
        self.setCentralWidget(central_widget)

        self.resize(1000, 600)

        # Worker thread setup
        self.worker = Worker(mutex, condition)
        # Slot now accepts a string argument for the initial text
        self.worker.request_input_signal.connect(self.edit_text_in_panel)
        self.worker.show_text_signal.connect(self.show_text_in_panel)

        # Define the request_text and show_text methods
        self._request_text = self.worker.edit_text_in_panel
        self.show_text = self.worker.show_text_in_panel

        # Connect UI elements
        for panel_name in PanelNames:
            if panel_name == PanelNames.PRODUCT:
                continue
            self.panels[panel_name].submit_button.clicked.connect(partial(self.submit_text, panel_name=panel_name))

        # Connect the MainWindow signal to the worker's slot
        self.send_text_signal.connect(self.worker.set_text_input)

    @classmethod
    def get_instance(cls):
        if cls.instance is None:
            mutex = QMutex()
            condition = QWaitCondition()
            cls.instance = cls(mutex, condition)
        return cls.instance

    def start_worker(self, func_to_run: Callable = None):
        # Start the worker thread
        self.worker.func_to_run = func_to_run
        self.worker.start()

    def initialize(self):
        self.show()

    def set_window_title(self, title):
        self.setWindowTitle(title)

    @Slot(PanelNames, str, str, dict)
    def edit_text_in_panel(self, panel_name: PanelNames, initial_text: str = '',
                     title: Optional[str] = None, optional_suggestions: Dict[str, str] = None) -> str:
        panel = self.panels[panel_name]
        if optional_suggestions is None:
            optional_suggestions = {}
        panel.edit_text(initial_text, title, list(optional_suggestions.values()))

    @Slot(PanelNames)
    def submit_text(self, panel_name: PanelNames):
        panel = self.panels[panel_name]
        text = panel.get_text()
        self.send_text_signal.emit(panel_name, text)

    @Slot(PanelNames, str)
    def show_text_in_panel(self, panel_name: PanelNames, text: str, is_html: bool = False):
        panel = self.panels[panel_name]
        panel.set_text(text, is_html)
