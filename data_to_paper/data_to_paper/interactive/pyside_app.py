from functools import partial
from typing import Optional, List, Collection, Dict, Callable, Any

from PySide6.QtGui import QTextOption
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QLabel, QPushButton, QWidget, \
    QHBoxLayout, QSplitter, QTextEdit, QTabWidget, QDialog, QSizePolicy
from PySide6.QtCore import Qt, QEventLoop, QMutex, QWaitCondition, QThread, Signal, Slot

from pygments.formatters.html import HtmlFormatter

from data_to_paper.conversation.stage import Stage
from data_to_paper.interactive.base_app import BaseApp
from data_to_paper.interactive.types import PanelNames
from data_to_paper.interactive.utils import open_file_on_os
from data_to_paper.research_types.scientific_research.scientific_stage import ScientificStage

MAKE_IT_UGLY_IN_MAC_BUT_MORE_CONSISTENT_ACROSS_OS = True

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
.markdown {
    font-family: Arial, sans-serif;
    font-size: 14px;
    color: white;
    overflow-wrap: break-word; /* Allows the words to break and wrap onto the next line */
    word-wrap: break-word; /* Older syntax, similar to overflow-wrap */
    white-space: normal; /* Overrides pre to allow wrapping */
    margin-bottom: 0.5em;
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

# three colors that go nicely together for h1, h2, h3:
# #0077cc, #0099cc, #00bbcc

# perhaps more distinct colors for h1, h2, h3:
# #0077cc, #0099cc, #00bbcc

BACKGROUND_COLOR = "#151515"
APP_BACKGROUND_COLOR = "#303030"

formatter = HtmlFormatter(style="monokai")
css = formatter.get_style_defs('.highlight')
additional_css = ".highlight, .highlight pre { background: " + BACKGROUND_COLOR + "; }"

# combine the CSS with the additional CSS:
CSS += css + additional_css


APP_STYLE = """
QMainWindow {
   background-color: black;
}
QScrollBar:vertical {
   border: 1px solid #999999;
   background: black;
   width: 10px;  # Adjust width for the vertical scrollbar
   margin: 0px 0px 0px 0px;
}
QScrollBar::handle:vertical {
   min-height: 10px;
   background-color: gray;  # Handle color
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
   background: none;  # Remove the arrows at the ends
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
   background: none;
}
QScrollBar:horizontal {
   border: 1px solid #999999;
   background: black;
   height: 10px;  # Adjust height for the horizontal scrollbar
   margin: 0px 0px 0px 0px;
}
QScrollBar::handle:horizontal {
   min-width: 10px;
   background-color: gray;  # Handle color
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
   background: none;  # Remove the arrows at the ends
}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
   background: none;
}
""".replace('black', APP_BACKGROUND_COLOR)

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


def _get_label_height(label: QLabel) -> int:
    """
    Get the height of a one-row QLabel.
    """
    return label.fontMetrics().height() + 2 * label.contentsMargins().top()


class Worker(QThread):
    # Signal now carries a string payload for initial text
    request_text_signal = Signal(PanelNames, str, str, str, dict)
    show_text_signal = Signal(PanelNames, str, bool)
    set_focus_on_panel_signal = Signal(PanelNames)
    advance_stage_signal = Signal(Stage)
    send_product_of_stage_signal = Signal(Stage, str)
    set_status_signal = Signal(PanelNames, int, str)
    set_header_signal = Signal(str)
    request_continue_signal = Signal()

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

    def worker_set_status(self, panel_name: PanelNames, position: int, status: str = ''):
        self.set_status_signal.emit(panel_name, position, status)

    def worker_set_header(self, header: str):
        self.set_header_signal.emit(header)

    def worker_request_text(self, panel_name: PanelNames, initial_text: str = '',
                            title: Optional[str] = None,
                            instructions: Optional[str] = None,
                            optional_suggestions: Dict[str, str] = None) -> str:
        self.mutex.lock()
        self.request_text_signal.emit(panel_name, initial_text, title, instructions, optional_suggestions)
        self.condition.wait(self.mutex)
        input_text = self._text_input
        self.mutex.unlock()
        return input_text

    def worker_request_continue(self):
        self.mutex.lock()
        self.request_continue_signal.emit()
        self.condition.wait(self.mutex)
        self.mutex.unlock()

    def worker_show_text(self, panel_name: PanelNames, text: str, is_html: bool = False):
        self.show_text_signal.emit(panel_name, text, is_html)

    def worker_set_focus_on_panel(self, panel_name: PanelNames):
        self.set_focus_on_panel_signal.emit(panel_name)

    def worker_advance_stage(self, stage: Stage):
        self.advance_stage_signal.emit(stage)

    def worker_send_product_of_stage(self, stage: Stage, product_text: str):
        self.send_product_of_stage_signal.emit(stage, product_text)

    @Slot(PanelNames, str)
    def receive_text_signal(self, panel_name, text):
        self.mutex.lock()
        self._text_input = text
        self._panel_name_input = panel_name
        self.condition.wakeAll()
        self.mutex.unlock()

    @Slot()
    def receive_continue_signal(self):
        self.mutex.lock()
        self.condition.wakeAll()
        self.mutex.unlock()


STEP_PANEL_BUTTON_STYLE = """
QPushButton {{
    background-color: {background_color};
    border-radius: 5px;
}}
QPushButton:pressed {{
    background-color: {pressed_color};
}}
"""


class StepsPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.labels_to_callbacks = None
        self.current_step = 0
        self.layout = QVBoxLayout(self)
        self.step_widgets = []

    def init_ui(self, labels_to_callbacks: Dict[str, Callable]):
        self.labels_to_callbacks = labels_to_callbacks
        for label, func in self.labels_to_callbacks.items():
            step_button = QPushButton(label)
            step_button.setFixedWidth(150)
            step_button.clicked.connect(func)
            self.layout.addWidget(step_button)
            self.step_widgets.append(step_button)
        self.layout.setSpacing(5)
        self.refresh()

    def refresh(self):
        for i, step in enumerate(self.step_widgets):
            if i == self.current_step:
                step.setStyleSheet(STEP_PANEL_BUTTON_STYLE.format(background_color="#FFA500", pressed_color="#FF8C00"))
            elif i < self.current_step:
                step.setStyleSheet(STEP_PANEL_BUTTON_STYLE.format(background_color="#008000", pressed_color="#006400"))
            else:
                step.setStyleSheet(STEP_PANEL_BUTTON_STYLE.format(background_color="#909090", pressed_color="#707070"))

    def set_step(self, step_name: str):
        self.current_step = list(self.labels_to_callbacks.keys()).index(step_name)
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
            right_label.setStyleSheet("color: #cc0000; font-size: 12px;")
            self.header_right_label = right_label
            header_tray.addWidget(right_label, alignment=Qt.AlignmentFlag.AlignRight)
        else:
            self.header_right_label = None

    def set_header(self, header: str):
        self.header = header
        self.header_label.setText(header)

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
        self.text_edit.setWordWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
        # self.text_edit.setFontPointSize(14)
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
        self.submit_button.setStyleSheet('QPushButton {background-color: #E3E0DA; color:' + BACKGROUND_COLOR + ';}')
        self.submit_button.clicked.connect(self.on_submit)
        self.buttons_tray.addWidget(self.submit_button)

        for i, button_text in enumerate(suggestion_button_names):
            button = QPushButton(button_text)
            button.setStyleSheet('QPushButton {background-color: #E3E0DA; color:' + BACKGROUND_COLOR + ';}')
            button.clicked.connect(self.on_suggestion_button_click)
            self.buttons_tray.addWidget(button)
            self.suggestion_buttons.append(button)
        self._set_buttons_visibility(False)

        self.loop = None
        if MAKE_IT_UGLY_IN_MAC_BUT_MORE_CONSISTENT_ACROSS_OS:
            self.setStyleSheet("color: white;")

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
        if MAKE_IT_UGLY_IN_MAC_BUT_MORE_CONSISTENT_ACROSS_OS:
            self.text_edit.setStyleSheet("color: orange; font-size: 14px; background-color: " + BACKGROUND_COLOR + ";")
        else:
            self.text_edit.setStyleSheet("color: orange; font-size: 14px; font-family: Arial;")

    def _set_html_text(self, text: str):
        # add the CSS to the HTML
        self.text_edit.setHtml(f'<style>{CSS}</style>{text}')
        if MAKE_IT_UGLY_IN_MAC_BUT_MORE_CONSISTENT_ACROSS_OS:
            self.text_edit.setStyleSheet("color: white; background-color: " + BACKGROUND_COLOR + ";")
        else:
            self.text_edit.setStyleSheet("color: white;")

    def set_text(self, text: str, is_html: bool = False):
        self.text_edit.setReadOnly(True)
        if is_html:
            self._set_html_text(text)
        else:
            self._set_plain_text(text)

    def set_instructions(self, instructions: str):
        self.instructions = instructions
        self.reset_instructions()

    def edit_text(self, text: Optional[str] = '',
                  title: Optional[str] = None,
                  instruction: Optional[str] = None,
                  suggestion_texts: Optional[List[str]] = None):
        self.text_edit.setReadOnly(False)
        self._set_plain_text(text)
        self._set_buttons_visibility(True)
        if suggestion_texts is not None:
            self.suggestion_texts = suggestion_texts
        self.set_instructions(instruction or '')
        self.set_header_right(title or '')
        self.loop = QEventLoop()
        self.loop.exec()

    def on_submit(self):
        self.text_edit.setReadOnly(True)
        self._set_buttons_visibility(False)
        self.set_header_right('')
        self.reset_instructions()
        if self.loop is not None:
            self.loop.exit()

    def get_text(self):
        return self.text_edit.toPlainText()


class HtmlPopup(QDialog):
    def __init__(self, title: str, html_content, parent=None):
        super(HtmlPopup, self).__init__(parent, Qt.WindowType.WindowCloseButtonHint)
        self.setWindowTitle(title)

        # Layout to organize widgets
        layout = QVBoxLayout()

        # QLabel to display HTML content
        label = QTextEdit()
        label.setReadOnly(True)
        label.setHtml(f'<style>{CSS}</style>{html_content}')

        # label.setText(html_content)
        # label.setTextFormat(Qt.RichText)  # Set the text format to RichText to enable HTML
        layout.addWidget(label)

        # QPushButton to close the dialog
        close_button = QPushButton("Close")
        if MAKE_IT_UGLY_IN_MAC_BUT_MORE_CONSISTENT_ACROSS_OS:
            close_button.setStyleSheet('QPushButton {background-color: #E3E0DA; color:' + BACKGROUND_COLOR + ';}')
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

        self.setLayout(layout)
        if MAKE_IT_UGLY_IN_MAC_BUT_MORE_CONSISTENT_ACROSS_OS:
            self.setStyleSheet("background-color: " + BACKGROUND_COLOR + ";")
        self.resize(800, 600)


def create_tabs(names_to_panels: Dict[str, Panel]):
    tabs = QTabWidget()
    for panel_name, panel in names_to_panels.items():
        tabs.addTab(panel, panel_name)
    return tabs


class PysideApp(QMainWindow, BaseApp):
    send_text_signal = Signal(str, PanelNames)
    send_continue_signal = Signal()
    a_application = None

    def __init__(self, mutex, condition, step_runner=None):
        super().__init__()
        self.q_application = None
        self.products: Dict[Stage, Any] = {}
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

        self.setStyleSheet(APP_STYLE)

        # Left side is a VBox with "Continue" button above and the steps panel below
        left_side = QVBoxLayout()
        self.layout.addLayout(left_side)

        # Continue button
        continue_button = QPushButton("Continue")
        continue_button.setEnabled(False)
        continue_button.setVisible(False)  # TODO: the Continue button is currently not used. Can be removed.

        continue_button.clicked.connect(self.upon_continue)
        left_side.addWidget(continue_button)
        self.continue_button = continue_button

        # Steps panel
        self.step_panel = StepsPanel()
        left_side.addWidget(self.step_panel)

        # Right side is a QHBoxLayout with a header on top and a splitter with the text panels below
        right_side = QVBoxLayout()
        self.layout.addLayout(right_side)

        # Header (html)
        self.header = QLabel()
        # set as HTML to allow for text highlighting
        self.header.setTextFormat(Qt.TextFormat.RichText)
        self.header.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        self.header.setStyleSheet("color: #005599; font-size: 24px; font-weight: bold;")
        right_side.addWidget(self.header)

        # Splitter with the text panels
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        left_splitter = QSplitter(Qt.Orientation.Vertical)
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        main_splitter.addWidget(left_splitter)
        main_splitter.addWidget(right_splitter)

        # Add the panels to the splitters (the top-right panel is a tab widget)
        self.tabs = create_tabs({'Response': self.panels[PanelNames.RESPONSE],
                                 'Product': self.panels[PanelNames.PRODUCT]})
        if MAKE_IT_UGLY_IN_MAC_BUT_MORE_CONSISTENT_ACROSS_OS:
            self.tabs.setStyleSheet(TABS_STYLE)
        else:
            self.tabs.setStyleSheet("QTabBar::tab { color: white; }")
        left_splitter.addWidget(self.panels[PanelNames.SYSTEM_PROMPT])
        left_splitter.addWidget(self.panels[PanelNames.MISSION_PROMPT])
        right_splitter.addWidget(self.tabs)
        right_splitter.addWidget(self.panels[PanelNames.FEEDBACK])
        left_splitter.setSizes([100, 500])
        right_side.setStretchFactor(main_splitter, 1)

        if MAKE_IT_UGLY_IN_MAC_BUT_MORE_CONSISTENT_ACROSS_OS:
            main_splitter.setStyleSheet("""
                QSplitter::handle {
                    width: 1px;
                    background-color: #202020;
                }
            """)

        right_side.addWidget(main_splitter)

        self.layout.addLayout(right_side)
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
        self.worker.set_header_signal.connect(self.upon_set_header)
        self.worker.request_continue_signal.connect(self.upon_request_continue)

        # Define the request_text and show_text methods
        self.request_text = self.worker.worker_request_text
        self.show_text = self.worker.worker_show_text
        self.set_focus_on_panel = self.worker.worker_set_focus_on_panel
        self.advance_stage = self.worker.worker_advance_stage
        self.send_product_of_stage = self.worker.worker_send_product_of_stage
        self._set_status = self.worker.worker_set_status
        self.set_header = self.worker.worker_set_header
        self.request_continue = self.worker.worker_request_continue

        # Connect UI elements
        for panel_name in PanelNames:
            if panel_name == PanelNames.PRODUCT:
                continue
            self.panels[panel_name].submit_button.clicked.connect(partial(self.submit_text, panel_name=panel_name))

        # Connect the MainWindow signal to the worker's slot
        self.send_text_signal.connect(self.worker.receive_text_signal)
        self.send_continue_signal.connect(self.worker.receive_continue_signal)

    @classmethod
    def get_instance(cls):
        if cls.instance is None:
            mutex = QMutex()
            condition = QWaitCondition()
            cls.instance = cls(mutex, condition)
        return cls.instance

    def start_worker(self):
        # Start the worker thread
        self.worker.func_to_run = self._run_all_steps
        self.worker.start()

    def initialize(self):
        self.step_panel.init_ui({stage.value: partial(self.show_product_for_stage, stage)
                                 for stage in self._get_all_steps()})
        self.show()
        self.start_worker()
        return self.q_application.exec()

    @Slot(PanelNames, int, str)
    def upon_set_status(self, panel_name: PanelNames, position: int, status: str = ''):
        if panel_name == PanelNames.PRODUCT or panel_name == PanelNames.RESPONSE:
            panel_name = [PanelNames.PRODUCT, PanelNames.RESPONSE]
        else:
            panel_name = [panel_name]
        for name in panel_name:
            if position == 1:
                self.panels[name].set_header_right(status)
            else:
                self.panels[name].set_header(status)
            self.panels[name].update()

    @Slot(str)
    def upon_set_header(self, header: str):
        self.header.setText(header)

    @Slot()
    def upon_request_continue(self):
        self.continue_button.setEnabled(True)

    @Slot()
    def upon_continue(self):
        self.continue_button.setEnabled(False)
        self.send_continue_signal.emit()

    def show_product_for_stage(self, stage: Stage):
        """
        Open a popup window to show the product of a stage.
        """
        product_text = self.products.get(stage, '<span style="color: white;">Not created yet.</span>')
        if product_text.startswith('<a href="file://'):
            # open the file in the normal OS application
            file_path = product_text.split('"')[1]
            open_file_on_os(file_path)
            return
        popup = HtmlPopup(stage.value, product_text)
        popup.show()
        self.popups.add(popup)
        popup.finished.connect(self.popup_closed)

    def popup_closed(self):
        closed_popup = self.sender()
        self.popups.discard(closed_popup)

    @Slot(PanelNames, str, str, dict)
    def upon_request_text(self, panel_name: PanelNames, initial_text: str = '',
                          title: Optional[str] = None,
                          instructions: Optional[str] = None,
                          optional_suggestions: Dict[str, str] = None):
        panel = self.panels[panel_name]
        if optional_suggestions is None:
            optional_suggestions = {}
        panel.edit_text(initial_text, title, instructions, list(optional_suggestions.values()))

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

    @Slot(Stage)
    def upon_advance_stage(self, stage: Stage):
        self.step_panel.set_step(stage.value)

    @Slot(Stage, str)
    def upon_send_product_of_stage(self, stage: Stage, product_text: str):
        self.products[stage] = product_text
