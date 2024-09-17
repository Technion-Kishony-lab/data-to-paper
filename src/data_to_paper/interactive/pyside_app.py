from functools import partial
from typing import Optional, List, Collection, Dict, Callable, Any, Union, Tuple

from PySide6.QtCore import Qt, QMutex, QWaitCondition, QThread, Signal, Slot
from PySide6.QtGui import QTextOption, QTextCursor
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QLabel, QPushButton, QWidget, \
    QHBoxLayout, QSplitter, QTextEdit, QTabWidget, QDialog, QSizePolicy, QCheckBox, QSpacerItem

from data_to_paper.conversation.stage import Stage
from data_to_paper.interactive.base_app import BaseApp, REQUESTING_MISSING_TEXT
from data_to_paper.interactive.enum_types import PanelNames
from data_to_paper.interactive.get_app import get_or_create_q_application_if_app_is_pyside
from data_to_paper.interactive.styles import CURRENT_STEP_COLOR, SUBMIT_BUTTON_COLOR, PANEL_HEADER_COLOR, QEDIT_STYLE, \
    STEP_PANEL_BUTTON_STYLE, BACKGROUND_COLOR, CSS, APP_STYLE, TABS_STYLE, HTMLPOPUP_STYLE, \
    MAIN_SPLITTER_STYLE, QCHECKBOX_STYLE, STEP_PANEL_RESET_BUTTON_STYLE
from data_to_paper.interactive.utils import open_file_on_os
from data_to_paper.servers.api_cost import StageToCost


def _get_label_height(label: QLabel) -> int:
    """
    Get the height of a one-row QLabel.
    """
    return label.fontMetrics().height() + 2 * label.contentsMargins().top()


class Worker(QThread):
    # Signal now carries a string payload for initial text
    request_panel_continue_signal = Signal(PanelNames)
    request_text_signal = Signal(PanelNames, str, str, str, str, dict)
    show_text_signal = Signal(PanelNames, str, bool, bool)
    set_focus_on_panel_signal = Signal(PanelNames)
    advance_stage_int_signal = Signal(int)
    send_product_of_stage_signal = Signal(Stage, str)
    set_status_signal = Signal(PanelNames, int, str)
    set_header_signal = Signal(str)
    send_api_usage_cost_signal = Signal(object)

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

    def worker_request_panel_continue(self, panel_name: PanelNames):
        self.mutex.lock()
        self.request_panel_continue_signal.emit(panel_name)
        self.condition.wait(self.mutex)
        self.mutex.unlock()

    def worker_request_text(self, panel_name: PanelNames, initial_text: str = '',
                            title: Optional[str] = None,
                            instructions: Optional[str] = None,
                            in_field_instructions: Optional[str] = None,
                            optional_suggestions: Dict[str, str] = None) -> str:
        self.mutex.lock()
        self.request_text_signal.emit(panel_name, initial_text, title, instructions, in_field_instructions,
                                      optional_suggestions)
        self.condition.wait(self.mutex)
        input_text = self._text_input
        self.mutex.unlock()
        return input_text

    def worker_show_text(self, panel_name: PanelNames, text: str, is_html: bool = False,
                         scroll_to_bottom: bool = False):
        self.show_text_signal.emit(panel_name, text, is_html, scroll_to_bottom)

    def worker_set_focus_on_panel(self, panel_name: PanelNames):
        self.set_focus_on_panel_signal.emit(panel_name)

    def worker_advance_stage_int(self, stage: int):
        self.advance_stage_int_signal.emit(stage)

    def worker_send_product_of_stage(self, stage: Stage, product_text: str):
        self.send_product_of_stage_signal.emit(stage, product_text)

    def worker_send_api_usage_cost(self, stages_to_costs: Dict[str, float]):
        self.send_api_usage_cost_signal.emit(stages_to_costs)

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

    @Slot(PanelNames)
    def receive_panel_continue_signal(self, panel_name):
        self.mutex.lock()
        self.condition.wakeAll()
        self.mutex.unlock()


class StepsPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.labels_to_callbacks = None
        self.current_step = 0
        self.layout = QVBoxLayout(self)
        self.step_widgets = {}

    def init_ui(self, labels_to_callbacks: Dict[Tuple[str, str, bool], Tuple[Callable, Callable]]):
        self.labels_to_callbacks = labels_to_callbacks
        for (label, name, resettable), (step_callback, reset_callback) in self.labels_to_callbacks.items():
            self.step_widgets[label] = QHBoxLayout()
            step_button = QPushButton(label)
            step_button.setFixedWidth(130)
            step_button.clicked.connect(step_callback)
            self.step_widgets[label].addWidget(step_button)
            if resettable:
                reset_to_step_button = QPushButton('↺')
                reset_to_step_button.setFixedWidth(20)
                reset_to_step_button.setStyleSheet(STEP_PANEL_RESET_BUTTON_STYLE.format(background_color="#909090",
                                                                                        pressed_color="#707070"))
                reset_to_step_button.clicked.connect(reset_callback)
                self.step_widgets[label].addWidget(reset_to_step_button)
            else:  # add a spacer to keep the layout consistent
                spacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
                self.step_widgets[label].addItem(spacer)
            self.layout.addLayout(self.step_widgets[label])
        self.layout.setSpacing(5)
        self.refresh()

    def refresh(self):
        for i, step in enumerate(self.step_widgets):
            if i == self.current_step:
                self.step_widgets[step].itemAt(0).widget().setStyleSheet(
                    STEP_PANEL_BUTTON_STYLE.format(background_color=CURRENT_STEP_COLOR,
                                                   pressed_color="#003377"))
                if self.step_widgets[step].itemAt(1).widget() is not None:
                    self.step_widgets[step].itemAt(1).widget().setEnabled(True)
            elif i < self.current_step:
                self.step_widgets[step].itemAt(0).widget().setStyleSheet(
                    STEP_PANEL_BUTTON_STYLE.format(background_color=SUBMIT_BUTTON_COLOR,
                                                   pressed_color="#006400"))
                if self.step_widgets[step].itemAt(1).widget() is not None:
                    self.step_widgets[step].itemAt(1).widget().setEnabled(True)
            else:
                self.step_widgets[step].itemAt(0).widget().setStyleSheet(
                    STEP_PANEL_BUTTON_STYLE.format(background_color="#909090", pressed_color="#707070"))
                # if the there is a reset button and not a spacer, disable the reset button
                if self.step_widgets[step].itemAt(1).widget() is not None:
                    self.step_widgets[step].itemAt(1).widget().setEnabled(False)

    def set_step_by_index(self, step_index: int):
        self.current_step = step_index
        self.refresh()

    def disable_refresh_of_all_steps(self):
        for step in self.step_widgets:
            if self.step_widgets[step].itemAt(1).widget() is not None:
                # set reset button to not visible
                self.step_widgets[step].itemAt(1).widget().setVisible(False)
                # add a spacer to keep the layout consistent
                spacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
                self.step_widgets[step].addItem(spacer)


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
        self.header_label.setStyleSheet(f"color: {PANEL_HEADER_COLOR}; font-size: 16px; font-weight: bold;")
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
        self.text_edit.setStyleSheet(QEDIT_STYLE)

        self.text_edit.setReadOnly(True)
        self.layout.addWidget(self.text_edit)

        # Instructions:
        self.instructions = None
        self.instructions_label = QLabel()
        self.update_instructions()
        self.layout.addWidget(self.instructions_label)

        # Buttons:
        self.buttons_tray = QHBoxLayout()
        self.layout.addLayout(self.buttons_tray)

        self.continue_button = QPushButton("Continue")
        self.continue_button.setVisible(False)
        self.continue_button.setStyleSheet('QPushButton {background-color: #E3E0DA; color:' + BACKGROUND_COLOR + ';}')
        self.continue_button.clicked.connect(self.on_continue)
        self.buttons_tray.addWidget(self.continue_button)

        self.submit_button = QPushButton("Submit")
        self.submit_button.setStyleSheet('QPushButton {background-color: ' + SUBMIT_BUTTON_COLOR + '; color:'
                                         + BACKGROUND_COLOR + ';}')
        self.submit_button.clicked.connect(self.on_submit)
        self.buttons_tray.addWidget(self.submit_button)

        for i, button_text in enumerate(suggestion_button_names):
            button = QPushButton(button_text)
            button.setStyleSheet('QPushButton {background-color: #E3E0DA; color:' + BACKGROUND_COLOR + ';}')
            button.clicked.connect(self.on_suggestion_button_click)
            self.buttons_tray.addWidget(button)
            self.suggestion_buttons.append(button)
        self._set_buttons_visibility(False)

        # self.setStyleSheet("color: white;")

    def _set_buttons_visibility(self, visible: bool):
        self.submit_button.setVisible(visible)
        self.instructions_label.setVisible(visible)
        for button in self.suggestion_buttons:
            button.setVisible(visible)

    def update_instructions(self):
        if self.instructions is not None:
            self.instructions_label.setText(self.instructions)
        else:
            self.instructions_label.setText('')
        self.instructions_label.setVisible(bool(self.instructions))

    def on_suggestion_button_click(self):
        button = self.sender()
        suggestion_index = self.suggestion_buttons.index(button)
        if suggestion_index >= len(self.suggestion_texts):
            return
        suggestion_text = self.suggestion_texts[suggestion_index]
        if suggestion_text is None:
            self.text_edit.setPlainText(REQUESTING_MISSING_TEXT)
            self.submit_button.click()
        else:
            self.text_edit.setPlainText(suggestion_text)

    def _set_plain_text(self, text: str):
        self.text_edit.setPlainText(text)

    def _set_html_text(self, text: str):
        # add the CSS to the HTML
        self.text_edit.setHtml(f'<style>{CSS}</style>{text}')

    def set_text(self, text: str, is_html: bool = False):
        self.text_edit.setReadOnly(True)
        if is_html:
            self._set_html_text(text)
        else:
            self._set_plain_text(text)

    def set_instructions(self, instructions: str):
        self.instructions = instructions
        self.update_instructions()

    def edit_text(self, text: Optional[str] = '',
                  title: Optional[str] = None,
                  instruction: Optional[str] = None,
                  in_field_instructions: Optional[str] = None,
                  suggestion_texts: Optional[List[str]] = None):
        self.text_edit.setReadOnly(False)
        if in_field_instructions:
            self.text_edit.setPlaceholderText(in_field_instructions)
        self._set_plain_text(text)
        self._set_buttons_visibility(True)
        if suggestion_texts is not None:
            self.suggestion_texts = suggestion_texts
        self.set_instructions(instruction or '')
        self.set_header_right(title or '')

    def scroll_to_bottom(self):
        self.text_edit.moveCursor(QTextCursor.End)
        self.text_edit.ensureCursorVisible()

    def wait_for_continue(self):
        self.continue_button.setVisible(True)

    def on_submit(self):
        self.text_edit.setReadOnly(True)
        self.text_edit.setPlaceholderText('')
        self._set_buttons_visibility(False)
        self.set_header_right('')
        self.set_instructions('')

    def on_continue(self):
        self.continue_button.setVisible(False)

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
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        layout.addWidget(self.close_button)

        self.setLayout(layout)
        self.setStyleSheet(HTMLPOPUP_STYLE)
        self.resize(800, 600)


def create_tabs(names_to_panels: Dict[str, Panel]):
    tabs = QTabWidget()
    for panel_name, panel in names_to_panels.items():
        tabs.addTab(panel, panel_name)
    return tabs


class APIUsageCostDialog(QDialog):
    def __init__(self, html_content, parent=None):
        super(APIUsageCostDialog, self).__init__(parent, Qt.WindowType.WindowCloseButtonHint)
        self.setWindowTitle("API Usage Cost")

        # Layout to organize widgets
        layout = QVBoxLayout()

        # QLabel to display HTML content
        label = QTextEdit()
        label.setReadOnly(True)
        label.setHtml(f'<style>{CSS}</style>{html_content}')

        layout.addWidget(label)

        # QPushButton to close the dialog
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        layout.addWidget(self.close_button)

        self.setLayout(layout)
        self.setStyleSheet(HTMLPOPUP_STYLE)
        self.resize(400, 300)


class PysideApp(QMainWindow, BaseApp):
    send_text_signal = Signal(str, PanelNames)
    send_panel_continue_signal = Signal(PanelNames)
    a_application = None

    def __init__(self, mutex, condition, step_runner=None):
        super().__init__()
        self.products: Dict[Stage, Any] = {}
        self.popups = set()
        self.api_usage_cost = StageToCost()

        self.panels = {
            PanelNames.SYSTEM_PROMPT: EditableTextPanel("System Prompt", "", ("Default",)),
            PanelNames.MISSION_PROMPT: EditableTextPanel("Mission Prompt", "", ("Default",)),
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

        # Steps panel
        self.step_panel = StepsPanel()
        left_side.addWidget(self.step_panel)

        # Right side is a QVBoxLayout with a header on top and a splitter with the text panels below
        right_side = QVBoxLayout()
        self.layout.addLayout(right_side)

        header_and_checkbox = QHBoxLayout()
        right_side.addLayout(header_and_checkbox)

        # Header:
        self.header = QLabel()
        self.header.setTextFormat(Qt.TextFormat.RichText)
        self.header.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.header.setStyleSheet(f"color: {CURRENT_STEP_COLOR}; font-size: 24px; font-weight: bold;")

        spacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        header_and_checkbox.addWidget(self.header)
        header_and_checkbox.addItem(spacer)

        # Checkboxes:
        check_boxes = QVBoxLayout()
        header_and_checkbox.addLayout(check_boxes)

        # Bypass-continue checkbox:
        self.bypass_continue_checkbox = QCheckBox("Auto continue")
        self.bypass_continue_checkbox.setChecked(False)
        self.bypass_continue_checkbox.setToolTip(
            "When unchecked, a user 'Continue' approval is required for each LLM iteration.\n"
            "When checked, the app only stops where explicit user choices are required.")
        self.bypass_continue_checkbox.setStyleSheet(QCHECKBOX_STYLE)
        check_boxes.addWidget(self.bypass_continue_checkbox)

        # Bypass-mission prompt checkbox:
        self.bypass_mission_prompt_checkbox = QCheckBox("Auto mission prompt")
        self.bypass_mission_prompt_checkbox.setChecked(False)
        self.bypass_mission_prompt_checkbox.setToolTip(
            "When unchecked, user can edit each mission prompt.\n"
            "When checked, the default mission prompt is automatically used.")
        self.bypass_mission_prompt_checkbox.setStyleSheet(QCHECKBOX_STYLE)
        check_boxes.addWidget(self.bypass_mission_prompt_checkbox)

        # add button with $ sign that opens the pricing dialog, displaying the api usage cost per stage
        self.api_usage_cost_button = QPushButton("")
        self.api_usage_cost_button.setFixedWidth(130)
        self._update_api_usage_cost_button()
        self.api_usage_cost_button.clicked.connect(self.show_api_usage_cost_dialog)
        header_and_checkbox.addWidget(self.api_usage_cost_button)

        # Splitter with the text panels
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        left_splitter = QSplitter(Qt.Orientation.Vertical)
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        main_splitter.addWidget(left_splitter)
        main_splitter.addWidget(right_splitter)

        # Add the panels to the splitters (the top-right panel is a tab widget)
        self.tabs = create_tabs({'Response': self.panels[PanelNames.RESPONSE],
                                 'Product': self.panels[PanelNames.PRODUCT]})
        self.tabs.setStyleSheet(TABS_STYLE)
        left_splitter.addWidget(self.panels[PanelNames.SYSTEM_PROMPT])
        left_splitter.addWidget(self.panels[PanelNames.MISSION_PROMPT])
        right_splitter.addWidget(self.tabs)
        right_splitter.addWidget(self.panels[PanelNames.FEEDBACK])
        left_splitter.setSizes([100, 500])
        right_side.setStretchFactor(main_splitter, 1)

        main_splitter.setStyleSheet(MAIN_SPLITTER_STYLE)
        right_side.addWidget(main_splitter)

        self.layout.addLayout(right_side)
        self.setCentralWidget(central_widget)

        self.resize(1000, 600)
        self.setWindowTitle("data-to-paper")

        # Worker thread setup
        self.worker = Worker(mutex, condition)
        # Slot now accepts a string argument for the initial text
        self.worker.request_panel_continue_signal.connect(self.upon_request_panel_continue)
        self.worker.request_text_signal.connect(self.upon_request_text)
        self.worker.show_text_signal.connect(self.upon_show_text)
        self.worker.set_focus_on_panel_signal.connect(self.upon_set_focus_on_panel)
        self.worker.advance_stage_int_signal.connect(self.upon_advance_stage_int)
        self.worker.send_product_of_stage_signal.connect(self.upon_send_product_of_stage)
        self.worker.set_status_signal.connect(self.upon_set_status)
        self.worker.set_header_signal.connect(self.upon_set_header)
        self.worker.send_api_usage_cost_signal.connect(self.upon_send_api_usage_cost)

        # Define the request_text and show_text methods
        self.request_panel_continue = self.worker.worker_request_panel_continue
        self.request_text = self.worker.worker_request_text
        self.show_text = self.worker.worker_show_text
        self.set_focus_on_panel = self.worker.worker_set_focus_on_panel
        self.send_product_of_stage = self.worker.worker_send_product_of_stage
        self._set_status = self.worker.worker_set_status
        self.set_header = self.worker.worker_set_header
        self.send_api_usage_cost = self.worker.worker_send_api_usage_cost

        # Connect UI elements
        for panel_name in PanelNames:
            if panel_name == PanelNames.PRODUCT:
                continue
            self.panels[panel_name].submit_button.clicked.connect(partial(self.submit_text, panel_name=panel_name))
            self.panels[panel_name].continue_button.clicked.connect(partial(self.upon_panel_continue,
                                                                            panel_name=panel_name))

        # Connect the MainWindow signal to the worker's slot
        self.send_text_signal.connect(self.worker.receive_text_signal)
        self.send_panel_continue_signal.connect(self.worker.receive_panel_continue_signal)

    def closeEvent(self, event):
        """Override the closeEvent to gracefully stop the worker thread."""
        print("Main window is closing...")
        for popup in self.popups:
            popup.close()
        self.stage_to_reset_to = True
        # imitate a button click if resetting when waiting for user input
        self._initiate_panel_button_clicks()
        if not self.worker.wait(5000):
            print("Worker thread did not finish in time. Forcefully terminating...")
        event.accept()

    @classmethod
    def get_instance(cls):
        if cls.instance is None:
            mutex = QMutex()
            condition = QWaitCondition()
            cls.instance = cls(mutex, condition)
        return cls.instance

    def advance_stage(self, stage: Union[Stage, int, bool]):
        if isinstance(stage, Stage):
            stage = list(self._get_stages()).index(stage)
        elif stage is True:  # completed
            stage = len(self._get_stages())
        elif stage is False:  # error
            stage = -1
        self.worker.worker_advance_stage_int(stage)

    def start_worker(self, func_to_run=None):
        # Start the worker thread
        self.worker.func_to_run = func_to_run or self._run_all_steps
        self.worker.start()

    def initialize(self, func_to_run=None):
        self.step_panel.init_ui(
            {(stage.value, stage.name, stage.resettable): (
                partial(self.show_product_for_stage, stage),
                partial(self.confirm_and_perform_reset_to_stage, stage)
            ) for stage in self._get_stages()})
        self.show()
        self.start_worker(func_to_run)
        return get_or_create_q_application_if_app_is_pyside().exec()

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

    def _update_api_usage_cost_button(self):
        cost = self.api_usage_cost.get_total_cost()
        self.api_usage_cost_button.setText(f"API Cost: ${cost:.2f}")

    def show_api_usage_cost_dialog(self):
        """
        Open a popup window to show the pricing of the API usage per stage.
        """
        popup = APIUsageCostDialog(self.api_usage_cost.as_html())
        popup.show()
        self.popups.add(popup)
        popup.finished.connect(self.popup_closed)

    def popup_closed(self):
        closed_popup = self.sender()
        self.popups.discard(closed_popup)

    @Slot(PanelNames)
    def upon_request_panel_continue(self, panel_name: PanelNames):
        if self.bypass_continue_checkbox.isChecked():
            self.send_panel_continue_signal.emit(panel_name)
        else:
            panel = self.panels[panel_name]
            panel.wait_for_continue()

    @Slot(PanelNames, str, str, dict)
    def upon_request_text(self, panel_name: PanelNames, initial_text: str = '',
                          title: Optional[str] = None,
                          instructions: Optional[str] = None,
                          in_field_instructions: Optional[str] = None,
                          optional_suggestions: Dict[str, str] = None):
        panel = self.panels[panel_name]
        if optional_suggestions is None:
            optional_suggestions = {}
        if panel_name == PanelNames.MISSION_PROMPT and self.bypass_mission_prompt_checkbox.isChecked():
            self.send_text_signal.emit(panel_name, initial_text)
            return
        panel.edit_text(initial_text, title, instructions, in_field_instructions, list(optional_suggestions.values()))

    @Slot(PanelNames)
    def upon_panel_continue(self, panel_name: PanelNames):
        self.send_panel_continue_signal.emit(panel_name)

    @Slot(PanelNames)
    def submit_text(self, panel_name: PanelNames):
        panel = self.panels[panel_name]
        text = panel.get_text()
        self.send_text_signal.emit(panel_name, text)

    @Slot(PanelNames, str, bool, bool)
    def upon_show_text(self, panel_name: PanelNames, text: str, is_html: bool = False,
                       scroll_to_bottom: bool = False):
        panel = self.panels[panel_name]
        panel.set_text(text, is_html)
        if scroll_to_bottom:
            panel.scroll_to_bottom()

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
    def upon_advance_stage_int(self, stage: int):
        self.step_panel.set_step_by_index(stage)

    @Slot(Stage, str)
    def upon_send_product_of_stage(self, stage: Stage, product_text: str):
        self.products[stage] = product_text

    @Slot(object)
    def upon_send_api_usage_cost(self, stages_to_costs: StageToCost):
        self.api_usage_cost = stages_to_costs
        self._update_api_usage_cost_button()

    def confirm_and_perform_reset_to_stage(self, stage: Stage):
        dialog = QDialog(self)
        dialog.setWindowTitle("Reset to Step")
        layout = QVBoxLayout(dialog)
        label = QLabel(f"Are you sure you want to reset to the '{stage.value}' step?\n"
                       f"This will irrevocably delete all progress after this step.")
        layout.addWidget(label)
        buttons_layout = QHBoxLayout()
        layout.addLayout(buttons_layout)
        yes_button = QPushButton("Yes")
        yes_button.clicked.connect(partial(self.perform_reset_to_stage, stage, dialog))
        no_button = QPushButton("No")
        no_button.clicked.connect(dialog.close)
        buttons_layout.addWidget(yes_button)
        buttons_layout.addWidget(no_button)
        dialog.exec()

    def perform_reset_to_stage(self, stage: Stage, dialog: Optional[QDialog] = None):
        if dialog is not None:
            dialog.close()

        self.stage_to_reset_to = stage

        # delete all product for stages after the reset stage
        stage_index = stage.get_index()
        stages = list(self._get_stages())
        for stage in stages[stage_index:]:
            self.products.pop(stage, None)
        # imitate a button click if resetting when waiting for user input
        self._initiate_panel_button_clicks()

    def _initiate_panel_button_clicks(self):
        for panel in self.panels.values():
            for button in [panel.submit_button, panel.continue_button]:
                if button.isVisible():
                    button.click()
