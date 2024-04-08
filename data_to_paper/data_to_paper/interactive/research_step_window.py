from functools import partial
from typing import Optional, List, Collection, Dict, Callable, Tuple

from PySide6.QtGui import QTextOption
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QLabel, QPushButton, QWidget, \
    QHBoxLayout, QSplitter, QTextEdit, QTabWidget, QDialog
from PySide6.QtCore import Qt, QEventLoop, QMutex, QWaitCondition, QThread, Signal, Slot

from pygments.formatters.html import HtmlFormatter

from data_to_paper.interactive.base_app import BaseApp
from data_to_paper.interactive.types import PanelNames
from data_to_paper.research_types.scientific_research.scientific_stage import SCIENTIFIC_STAGES_TO_NICE_NAMES, \
    ScientificStages

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
h1 {
    color: #0066cc;
}
h2 {
    color: #0099cc;
}
h3 {
    color: #00cccc;
}
'''

# three colors that go nicely together for h1, h2, h3:
# #0077cc, #0099cc, #00bbcc

# perhaps more distinct colors for h1, h2, h3:
# #0077cc, #0099cc, #00bbcc

BACKGROUND_COLOR = "#151515"

formatter = HtmlFormatter(style="monokai")
css = formatter.get_style_defs('.highlight')
additional_css = ".highlight, .highlight pre { background: " + BACKGROUND_COLOR + "; }"

# combine the CSS with the additional CSS:
CSS += css + additional_css


def _get_label_height(label: QLabel) -> int:
    """
    Get the height of a one-row QLabel.
    """
    return label.fontMetrics().height() + 2 * label.contentsMargins().top()


class Worker(QThread):
    # Signal now carries a string payload for initial text
    request_text_signal = Signal(PanelNames, str, str, dict)
    show_text_signal = Signal(PanelNames, str, bool)
    set_focus_on_panel_signal = Signal(PanelNames)
    advance_stage_signal = Signal(str)
    send_product_of_stage_signal = Signal(str, str)
    set_status_signal = Signal(str)

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

    def worker_set_status(self, status: str):
        self.set_status_signal.emit(status)

    def worker_request_text(self, panel_name: PanelNames, initial_text: str = '',
                           title: Optional[str] = None, optional_suggestions: Dict[str, str] = None) -> str:
        self.mutex.lock()
        self.request_text_signal.emit(panel_name, initial_text, title, optional_suggestions)
        self.condition.wait(self.mutex)
        input_text = self._text_input
        self.mutex.unlock()
        return input_text

    def worker_show_text(self, panel_name: PanelNames, text: str, is_html: bool = False):
        self.show_text_signal.emit(panel_name, text, is_html)

    def worker_set_focus_on_panel(self, panel_name: PanelNames):
        self.set_focus_on_panel_signal.emit(panel_name)

    def worker_advance_stage(self, stage):
        self.advance_stage_signal.emit(stage)

    def worker_send_product_of_stage(self, stage, product_text):
        self.send_product_of_stage_signal.emit(stage, product_text)

    @Slot(PanelNames, str)
    def set_text_input(self, panel_name, text):
        self.mutex.lock()
        self._text_input = text
        self._panel_name_input = panel_name
        self.condition.wakeAll()
        self.mutex.unlock()


class StepsPanel(QWidget):
    def __init__(self, names_labels_to_callbacks: List[Tuple[str, str, Callable]]):
        super().__init__()
        self.names_labels_to_callbacks = names_labels_to_callbacks
        self.current_step = 0
        self.layout = QVBoxLayout(self)
        self.step_widgets = []
        self.init_ui()
        self.refresh()

    def init_ui(self):
        for name, label, func in self.names_labels_to_callbacks:
            step_button = QPushButton(label)
            step_button.setFixedWidth(150)
            step_button.clicked.connect(func)
            self.layout.addWidget(step_button)
            self.step_widgets.append(step_button)
        self.layout.setSpacing(5)

    def refresh(self):
        template = """
QPushButton {{
    background-color: {background_color};
    border-radius: 5px;
}}
QPushButton:pressed {{
    background-color: {pressed_color};
}}
"""
        for i, step in enumerate(self.step_widgets):
            if i == self.current_step:
                step.setStyleSheet(template.format(background_color="#FFA500", pressed_color="#FF8C00"))
            elif i < self.current_step:
                step.setStyleSheet(template.format(background_color="#008000", pressed_color="#006400"))
            else:
                step.setStyleSheet(template.format(background_color="#909090", pressed_color="#707070"))

    def set_step(self, step_name):
        self.current_step = list(name for name, _, __ in self.names_labels_to_callbacks).index(step_name)
        self.refresh()

    def advance_progress(self):
        self.current_step += 1
        if self.current_step >= len(self.step_widgets):
            self.current_step = 0
        self.refresh()


class Panel(QWidget):
    def __init__(self, header: Optional[str] = None, header_right: Optional[str] = None):
        """
        A panel that displays text and allows editing.
        """
        super().__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        header_tray = QHBoxLayout()
        self.layout.addLayout(header_tray)

        self.header = header
        label = QLabel(header)
        label.setFixedHeight(_get_label_height(label))
        self.header_label = label
        self.header_label.setStyleSheet("color: #0077cc; font-size: 16px; font-weight: bold;")
        header_tray.addWidget(label)

        self.header_right = header_right
        if header_right is not None:
            right_label = QLabel(header_right)
            right_label.setFixedHeight(_get_label_height(right_label))
            right_label.setStyleSheet("color: #cc0000; font-size: 16px; font-weight: bold;")
            self.header_right_label = right_label
            header_tray.addWidget(right_label, alignment=Qt.AlignRight)
        else:
            self.header_right_label = None

    def set_header_right(self, text: str):
        if self.header_right_label is None:
            return
        self.header_right = text
        self.header_right_label.setText(text)

    def set_text(self, text):
        pass

    def get_text(self):
        pass


class EditableTextPanel(Panel):
    def __init__(self, header: str, header_right: Optional[str] = None,
                 suggestion_button_names: Optional[Collection[str]] = None):
        super().__init__(header, header_right)
        if suggestion_button_names is None:
            suggestion_button_names = []
        self.suggestion_button_names = suggestion_button_names
        self.suggestion_buttons = []
        self.suggestion_texts = [''] * len(suggestion_button_names)

        self.text_edit = QTextEdit()
        self.text_edit.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        self.text_edit.setFontPointSize(14)
        self.text_edit.setStyleSheet("background-color: " + BACKGROUND_COLOR + ";")

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
        if visible:
            self.set_header_right('Input required')
        else:
            self.set_header_right('')

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


class HtmlPopup(QDialog):
    def __init__(self, title: str, html_content, parent=None):
        super(HtmlPopup, self).__init__(parent, Qt.WindowCloseButtonHint)
        self.setWindowTitle(title)

        # Layout to organize widgets
        layout = QVBoxLayout()

        # QLabel to display HTML content
        label = QTextEdit()
        label.setReadOnly(True)
        label.setHtml(f'<style>{CSS}</style>{html_content}')

        print(f'TITLE: {title}\nHTML_CONTENT: {html_content}')
        print(f'HTML_STYLE: {CSS}')

        # label.setText(html_content)
        # label.setTextFormat(Qt.RichText)  # Set the text format to RichText to enable HTML
        layout.addWidget(label)

        # QPushButton to close the dialog
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

        self.setLayout(layout)
        self.resize(800, 600)


def create_tabs(names_to_panels: Dict[str, Panel]):
    tabs = QTabWidget()
    for panel_name, panel in names_to_panels.items():
        tabs.addTab(panel, panel_name)
    return tabs


class ResearchStepApp(QMainWindow, BaseApp):
    send_text_signal = Signal(str, PanelNames)

    def __init__(self, mutex, condition):
        super().__init__()
        self.products = {}
        self.popups = set()

        self.panels = {
            PanelNames.SYSTEM_PROMPT: EditableTextPanel("System Prompt", "", ("Default", )),
            PanelNames.MISSION_PROMPT: EditableTextPanel("Mission Prompt", "", ("Default", )),
            PanelNames.RESPONSE: EditableTextPanel("Response", "", ()),
            PanelNames.PRODUCT: EditableTextPanel("Product", "", ()),
            PanelNames.FEEDBACK: EditableTextPanel("Feedback", "", ("AI Review", "No comments")),
        }
        central_widget = QWidget()
        self.layout = QHBoxLayout(central_widget)

        self.step_panel = StepsPanel([(stage, label, partial(self.show_product_for_stage, stage))
                                      for stage, label in SCIENTIFIC_STAGES_TO_NICE_NAMES.items()])
        self.layout.addWidget(self.step_panel)

        main_splitter = QSplitter(Qt.Horizontal)
        left_splitter = QSplitter(Qt.Vertical)
        left_splitter.setHandleWidth(5)
        right_splitter = QSplitter(Qt.Vertical)

        self.tabs = create_tabs({'Response': self.panels[PanelNames.RESPONSE],
                                 'Product': self.panels[PanelNames.PRODUCT]})

        left_splitter.addWidget(self.panels[PanelNames.SYSTEM_PROMPT])
        left_splitter.addWidget(self.panels[PanelNames.MISSION_PROMPT])
        right_splitter.addWidget(self.tabs)
        right_splitter.addWidget(self.panels[PanelNames.FEEDBACK])

        main_splitter.addWidget(left_splitter)
        main_splitter.addWidget(right_splitter)

        left_splitter.setSizes([100, 400])
        self.layout.addWidget(main_splitter)
        self.setCentralWidget(central_widget)

        self.resize(1000, 600)
        self.setWindowTitle("data-to-paper")

        # Worker thread setup
        self.worker = Worker(mutex, condition)
        # Slot now accepts a string argument for the initial text
        self.worker.request_text_signal.connect(self.upon_request_text)
        self.worker.show_text_signal.connect(self.upon_show_text)
        self.worker.set_focus_on_panel_signal.connect(self.upon_set_focus_on_panel)
        self.worker.advance_stage_signal.connect(self.upon_advance_stage)
        self.worker.send_product_of_stage_signal.connect(self.upon_send_product_of_stage)
        self.worker.set_status_signal.connect(self.upon_set_status)

        # Define the request_text and show_text methods
        self.request_text = self.worker.worker_request_text
        self.show_text = self.worker.worker_show_text
        self.set_focus_on_panel = self.worker.worker_set_focus_on_panel
        self.advance_stage = self.worker.worker_advance_stage
        self.send_product_of_stage = self.worker.worker_send_product_of_stage
        self.set_status = self.upon_set_status

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

    def upon_set_status(self, status: str):
        print(f"Setting status: {status}")
        self.panels[PanelNames.RESPONSE].set_header_right(status)
        self.panels[PanelNames.PRODUCT].set_header_right(status)
        # it does not get updated. so we need to call update() to update the header_right:
        self.panels[PanelNames.RESPONSE].update()
        self.panels[PanelNames.PRODUCT].update()

    def _get_product_name(self, stage):
        return SCIENTIFIC_STAGES_TO_NICE_NAMES[stage]

    def show_product_for_stage(self, stage):
        """
        Open a popup window to show the product of a stage.
        """
        print(f"Showing product for stage: {stage}")
        product_text = self.products.get(stage, 'Not created yet.')
        popup = HtmlPopup(self._get_product_name(stage), product_text)
        popup.show()
        self.popups.add(popup)
        popup.finished.connect(self.popup_closed)

    def popup_closed(self):
        closed_popup = self.sender()
        self.popups.discard(closed_popup)

    @Slot(PanelNames, str, str, dict)
    def upon_request_text(self, panel_name: PanelNames, initial_text: str = '',
                          title: Optional[str] = None, optional_suggestions: Dict[str, str] = None):
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
    def upon_show_text(self, panel_name: PanelNames, text: str, is_html: bool = False):
        panel = self.panels[panel_name]
        panel.set_text(text, is_html)

    @Slot(PanelNames)
    def upon_set_focus_on_panel(self, panel_name: PanelNames):
        panel = self.panels[panel_name]
        panel.text_edit.setFocus()
        # if the panel is in a tab, switch to the tab
        for i in range(self.tabs.count()):
            if self.tabs.widget(i) == panel:
                self.tabs.setCurrentIndex(i)
                break

    @Slot(str)
    def upon_advance_stage(self, stage):
        self.step_panel.set_step(stage)

    @Slot(str, str)
    def upon_send_product_of_stage(self, stage, product_text):
        self.products[stage] = product_text
