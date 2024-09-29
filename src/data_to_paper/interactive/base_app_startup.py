from __future__ import annotations

import sys
from functools import partial
from pathlib import Path
from typing import List, Tuple, Type, Optional, TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, \
    QMessageBox, QWidget, QHBoxLayout, QSizePolicy, QFrame, QCheckBox, QComboBox

from data_to_paper.base_products.file_descriptions import TEXT_EXTS
from data_to_paper.env import BASE_FOLDER

from .base_widgets import PlainTextPasteTextEdit
from .get_app import get_or_create_q_application_if_app_is_pyside
from .styles import SCROLLBAR_STYLE, QCHECKBOX_STYLE

if TYPE_CHECKING:
    from data_to_paper.base_steps import BaseStepsRunner

BASE_PROJECT_DIRECTORY = BASE_FOLDER / 'projects'


def get_relative_path(base_path, target_path):
    """
    Get the relative path from base_path to target_path. Allowing for .. in the path.
    """
    base_parts = base_path.parts
    target_parts = target_path.parts
    common_length = 0
    for base_part, target_part in zip(base_parts, target_parts):
        if base_part != target_part:
            break
        common_length += 1
    back_steps = len(base_parts) - common_length
    forward_steps = target_parts[common_length:]
    return Path(*(['..'] * back_steps + list(forward_steps)))


style_sheet = """
QWidget {
    background-color: #404040; /* Application Background Color */
    color: white;
    font-family: Arial, Arial;
    font-size: 14pt;
}

QPushButton {
    background-color: #6060a0;
    border: none;
    color: #ffffff; /* White */
    padding: 10px 24px;
    text-align: center;
    text-decoration: none;
    font-size: 16px;
    margin: 4px 2px;
    border-radius: 12px;
}

QPushButton:hover {
    background-color: #7070c0;
}

QPushButton:pressed {
    background-color: #505080;
}

QPushButton:disabled {
    background-color: #606060;
}

QComboBox {
    background-color: #151515;
    color: white;
    border: 1px solid #606060;
    border-radius: 5px;
    padding: 5px;
}

QLineEdit {
    height: 25px; /* Adjust the height here */
    padding: 5px 10px;
}
""" + SCROLLBAR_STYLE

text_box_style = "background-color: #151515; color: white;"


def create_info_label(tooltip_text):
    info_label = QLabel("ℹ️")
    info_label.setToolTip(tooltip_text)
    return info_label


class FileWidget(QWidget):
    def __init__(self, abs_project_directory: Optional[Path], file_number: int, file_path='', is_binary=False,
                 description='', on_change=lambda: None):
        super().__init__()
        self._abs_project_directory = abs_project_directory
        self._abs_file_path = None

        file_input_widget = QFrame()  # Create a QFrame for encapsulating the file input widget
        file_input_widget.setFrameShape(QFrame.Box)  # noqa
        file_input_widget.setFrameShadow(QFrame.Plain)  # noqa

        layout = QVBoxLayout(file_input_widget)  # Maintain horizontal layout
        self.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)

        file_path_tray = QHBoxLayout()

        description_info = create_info_label(
            "Add a data file by clicking the 'Browse' button.\n"
            "Provide a description of the file, including the type of data and attribute names.")
        file_path_tray.addWidget(description_info)

        file_label_widget = QLabel(f"File #{file_number}:")
        file_path_tray.addWidget(file_label_widget)
        self.file_label_widget = file_label_widget

        file_path_widget = QLineEdit()
        file_path_widget.setReadOnly(True)
        file_path_widget.setStyleSheet(text_box_style)
        file_path_tray.addWidget(file_path_widget)
        self.file_path_widget = file_path_widget

        is_binary_checkbox = QCheckBox("Binary")
        is_binary_checkbox.setStyleSheet(QCHECKBOX_STYLE)
        is_binary_checkbox.setChecked(is_binary)
        file_path_tray.addWidget(is_binary_checkbox)
        self.is_binary_checkbox = is_binary_checkbox

        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_files)
        file_path_tray.addWidget(browse_button)
        self.browse_button = browse_button

        remove_button = QPushButton("Delete")
        file_path_tray.addWidget(remove_button)
        self.remove_button = remove_button

        layout.addLayout(file_path_tray)

        description_edit = PlainTextPasteTextEdit()
        description_edit.setPlaceholderText("Enter file description here...")
        description_edit.setStyleSheet(text_box_style)
        description_edit.setPlainText(description)
        layout.addWidget(description_edit)
        self.description_edit = description_edit

        self.set_file_path(file_path)

        self.file_path_widget.textChanged.connect(on_change)
        self.description_edit.textChanged.connect(on_change)

    @property
    def abs_path(self) -> str:
        return self._abs_file_path

    @property
    def abs_or_rel_path(self) -> str:
        return self._convert_abs_file_path_to_abs_or_rel(self._abs_file_path)

    @property
    def is_binary(self) -> bool:
        return self.is_binary_checkbox.isChecked()

    @property
    def description(self) -> str:
        return self.description_edit.toPlainText()

    def setDisabled(self, disable: bool):
        self.is_binary_checkbox.setDisabled(disable)
        self.browse_button.setDisabled(disable)
        self.remove_button.setDisabled(disable)
        self.description_edit.setReadOnly(disable)

    def browse_files(self):
        search_in = str(BASE_PROJECT_DIRECTORY) if self._abs_project_directory is None \
            else str(self._abs_project_directory)
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select a data file", search_in,
            "CSV Files (*.csv);;TEXT Files (*.txt);;Excel Files (*.xlsx, *.xls);;ZIP Files (*.zip);;All Files (*)")
        if file_path:
            file_path = file_path.replace('.zip', '')
            self.set_file_path(file_path)
            self.set_is_binary()

    def set_is_binary(self, is_binary: Optional[bool] = None):
        """
        Set the is_binary checkbox. If is_binary is None, it will be determined based on the file extension.
        """
        if is_binary is None:
            if self._abs_file_path:
                ext = self._abs_file_path.split('.')[-1]
                is_binary = '.' + ext not in TEXT_EXTS
            else:
                is_binary = False
        self.is_binary_checkbox.setChecked(is_binary)

    def set_file_path(self, file_path: str):
        """
        Set the file path. If the path is relative, it will be converted to an absolute path,
        relative to the project directory.
        """
        if not file_path:
            file_path = None
        else:
            file_path = Path(file_path)
            if not file_path.is_absolute():
                if self._abs_project_directory is None:
                    raise ValueError("Project directory is not set.")
                file_path = self._abs_project_directory / file_path
            file_path = str(file_path)
        self._abs_file_path = file_path
        self._refresh_file_path()

    def set_project_directory(self, abs_project_directory: Optional[Path]):
        self._abs_project_directory = abs_project_directory
        self._refresh_file_path()

    def _refresh_file_path(self):
        file_path = self._convert_abs_file_path_to_abs_or_rel(self._abs_file_path)
        self.file_path_widget.setText(file_path)

    def _convert_abs_file_path_to_abs_or_rel(self, abs_file_path: str) -> str:
        if not abs_file_path:
            return ''
        abs_file_path = Path(abs_file_path)
        if self._abs_project_directory is not None:
            try:
                abs_file_path = get_relative_path(self._abs_project_directory, abs_file_path)
            except ValueError:
                pass
        return str(abs_file_path)


class MultiFileWidget(QWidget):
    def __init__(self, abs_project_directory: Optional[Path] = None, file_paths: List[str] = None,
                 is_binary: List[bool] = None, descriptions: List[str] = None, on_change=lambda: None):
        file_paths = file_paths or []
        is_binary = is_binary or []
        descriptions = descriptions or []
        super().__init__()

        self.current_file_widget = None
        self.file_widgets = []

        self._abs_project_directory = abs_project_directory
        layout = QVBoxLayout()

        # Create a horizontal layout for the pulldown menu and file count label
        header_layout = QHBoxLayout()

        # Create the ComboBox (dropdown) to list files
        self.file_selector = QComboBox()
        self.file_selector.currentIndexChanged.connect(self.display_selected_file)

        # Set the size policy to make the ComboBox extend to the right as far as possible
        self.file_selector.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        header_layout.addWidget(self.file_selector)

        # Create a label to show the total number of files
        self.file_count_label = QLabel(f"")
        self.update_file_count()
        self.file_count_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)  # Fixed size for the label
        header_layout.addWidget(self.file_count_label)

        # Add Another File button
        self.add_file_button = QPushButton("Add Another File")
        self.add_file_button.clicked.connect(self.add_file)
        self.add_file_button.setFixedWidth(200)  # prevent button from expanding
        header_layout.addWidget(self.add_file_button, alignment=Qt.AlignmentFlag.AlignRight)

        # Add the header layout to the main layout
        layout.addLayout(header_layout)

        # Area to display the selected FileWidget
        self.file_display_area = QVBoxLayout()
        layout.addLayout(self.file_display_area)

        self.setLayout(layout)
        for file_path, is_bin, description in zip(file_paths, is_binary, descriptions):
            self.add_file(file_path, is_bin, description)
        self.on_change = on_change

    def get_all_file_widgets(self) -> List[FileWidget]:
        return self.file_widgets

    def add_file(self, abs_file_path='', is_binary=False, description=''):
        new_file_widget = FileWidget(self._abs_project_directory, len(self.file_widgets) + 1,
                                     file_path=abs_file_path, is_binary=is_binary, description=description,
                                     on_change=self.on_change)
        new_file_widget.browse_button.clicked.connect(self.on_browse)
        self.file_widgets.append(new_file_widget)
        new_file_widget.remove_button.clicked.connect(partial(self._remove_file, new_file_widget))

        self.update_file_count()
        self._update_file_labels(len(self.file_widgets) - 1)
        self.display_selected_file(len(self.file_widgets) - 1)
        self.on_change()

    def on_browse(self, file_widget: FileWidget):
        self._update_file_labels()

    def display_selected_file(self, index: int):
        if self.current_file_widget:
            self.file_display_area.removeWidget(self.current_file_widget)
            self.current_file_widget.hide()  # Hide the current widget
        if index < 0 or index >= len(self.file_widgets):
            self.current_file_widget = None
            return
        self.current_file_widget = self.get_all_file_widgets()[index]
        self.current_file_widget.show()
        self.file_display_area.addWidget(self.current_file_widget)

    def set_project_directory(self, abs_project_directory: Optional[Path]):
        self._abs_project_directory = abs_project_directory
        for file_widget in self.get_all_file_widgets():
            file_widget.set_project_directory(abs_project_directory)

    def _remove_file(self, widget):
        index = self.get_all_file_widgets().index(widget)
        # widget.destroyed.connect(self._update_file_labels)
        widget.deleteLater()
        self.file_widgets.remove(widget)

        self.update_file_count()
        index = min(index, len(self.file_widgets) - 1)
        self._update_file_labels(index)
        self.display_selected_file(index)
        self.on_change()

    def _update_file_labels(self, index: Optional[int] = None):
        """Update the labels of the files in the ComboBox."""
        for i, file_widget in enumerate(self.get_all_file_widgets()):
            file_widget.file_label_widget.setText(f"File #{i + 1}:")
        index = index if index is not None else self.file_selector.currentIndex()
        self.file_selector.blockSignals(True)
        self.file_selector.clear()
        for i, file_widget in enumerate(self.file_widgets):
            abs_file_path = file_widget.abs_path if file_widget.abs_path else ''
            file_name = self._get_file_display_name(i + 1, abs_file_path)
            self.file_selector.addItem(file_name)
        self.file_selector.setCurrentIndex(index)
        self.file_selector.blockSignals(False)

    def update_file_count(self):
        """Update the total number of files label."""
        self.file_count_label.setText(f"Total number of files: {len(self.file_widgets)}")

    def _get_file_display_name(self, file_number: int, abs_file_path: str) -> str:
        """Return the display name for the file in the format 'File #X: <file_stem>'."""
        s = f"File #{file_number}"
        if abs_file_path:
            file_stem = Path(abs_file_path).name  # Get the full file name (including extension)
            s += f": {file_stem}"
        return s

    def setDisabled(self, disable: bool):
        self.add_file_button.setDisabled(disable)
        for file_widget in self.get_all_file_widgets():
            file_widget.setDisabled(disable)

    def clear(self, num_files=1):
        """Clear all the file widgets and reset with a specified number of empty file slots."""
        # Clear all existing file widgets
        self.file_widgets.clear()
        self.file_selector.clear()

        # Remove widgets from the display area
        while self.file_display_area.count():
            widget = self.file_display_area.takeAt(0).widget()
            if widget:
                widget.deleteLater()
        for _ in range(num_files):
            self.add_file()

        # Update the file count label
        self.update_file_count()


class SingleFileWidget(MultiFileWidget):
    """
    Allows only one file.
    Do not show the 'Add Another File' button.
    Do not allow removing the file.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_file_button.hide()

    def add_file(self, abs_file_path='', is_binary=False, description=''):
        if self.files_layout.count() > 0:
            return
        super().add_file(abs_file_path, is_binary, description)
        self.get_all_file_widgets()[0].remove_button.hide()


class TextEditWithHeader(QWidget):
    def __init__(self, title: str, help_text: str = '', text: str = '', on_change=lambda: None):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(QLabel(title))
        text_edit = PlainTextPasteTextEdit()
        text_edit.setPlaceholderText(help_text)
        text_edit.setStyleSheet(text_box_style)
        text_edit.setPlainText(text)
        layout.addWidget(text_edit)
        self.text_edit = text_edit
        self.text_edit.textChanged.connect(on_change)  # Connect signal to callback

    def clear(self):
        self.text_edit.clear()

    def setPlainText(self, text):  # noqa for consistency with QTextEdit
        self.text_edit.setPlainText(text)

    def toPlainText(self):  # noqa for consistency with QTextEdit
        return self.text_edit.toPlainText()

    def setDisabled(self, disable: bool):
        self.text_edit.setReadOnly(disable)


class BaseStartDialog(QDialog):
    def __init__(self, steps_runner_cls: Type[BaseStepsRunner] = None,
                 project_directory: Optional[Path] = None):
        super().__init__()
        self.steps_runner_cls = steps_runner_cls
        self.current_config = {}
        self.is_locked = False
        self._abs_project_directory = None

        self._set_style()
        self.layout = QVBoxLayout(self)
        self.layout.addLayout(self._create_project_name_layout())
        self.widgets = self._create_widgets()
        for widget in self.widgets.values():
            self.layout.addWidget(widget)
        self.layout.addLayout(self._create_start_exist_buttons_layout())

        self._initialize(project_directory)

    def _create_widgets(self):
        return {}

    def _set_style(self):
        self.setWindowTitle(f"data-to-paper: Set and Run Project ({self.steps_runner_cls.name})")
        self.resize(1000, 1000)
        self.setStyleSheet(style_sheet)

    def _initialize(self, project_directory: Optional[Path]):
        self._clear_all()
        if project_directory:
            try:
                self.open_project(project_directory)
            except FileNotFoundError:
                self._clear_all()
                QMessageBox.warning(self, "Invalid Directory",
                                    f"The app was started with an invalid project directory:\n{project_directory}.\n"
                                    f"Please select a valid project directory.")

    def _create_project_name_layout(self):
        project_name_layout = QHBoxLayout()
        self.project_folder_header = QLabel("Project:")
        project_name_layout.addWidget(self.project_folder_header)
        self.project_folder_label = QLabel()
        self.project_folder_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        project_name_layout.addWidget(self.project_folder_label)
        self.open_button = QPushButton("Open")
        self.open_button.clicked.connect(lambda _: self.open_project())
        project_name_layout.addWidget(self.open_button)
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_project)
        project_name_layout.addWidget(self.save_button)
        self.new_button = QPushButton("New")
        self.new_button.clicked.connect(self._clear_all)
        project_name_layout.addWidget(self.new_button)
        return project_name_layout

    def _create_start_exist_buttons_layout(self):
        buttons_tray = QHBoxLayout()

        start_button = QPushButton("Save and Start")
        start_button.clicked.connect(self.on_start_clicked)
        start_button.setDisabled(True)
        buttons_tray.addWidget(start_button)

        close_button = QPushButton("Exit")
        close_button.clicked.connect(self.close_app)
        buttons_tray.addWidget(close_button)

        return buttons_tray

    def _clear_all(self):
        self._set_project_directory(None)
        for widget in self.widgets.values():
            widget.clear()
        self._lock_project_for_editing(disable=False)
        self.current_config = {}

    def close_app(self):
        self.reject()
        QApplication.instance().exit()  # Exit the application

    def _lock_project_for_editing(self, disable=True):
        self.is_locked = disable
        self.project_folder_header.setText("Project [LOCKED]:" if disable else "Project:")
        self.save_button.setDisabled(disable)
        for widget in self.widgets.values():
            widget.setDisabled(disable)

    """Save project"""

    def _check_project(self) -> bool:
        # config = self._convert_widgets_to_config()
        return True

    def _browse_for_new_project_directory(self) -> Optional[Path]:
        dialog = QFileDialog(self, "Save Project: Select or create an empty directory",
                             str(BASE_PROJECT_DIRECTORY))
        dialog.setFileMode(QFileDialog.Directory)  # noqa
        dialog.setOption(QFileDialog.ShowDirsOnly, True)  # noqa
        dialog.setAcceptMode(QFileDialog.AcceptOpen)  # noqa
        if dialog.exec() != QFileDialog.Accepted:  # noqa
            return
        project_directory = Path(dialog.selectedFiles()[0])
        # check that the project directory is empty:
        if list(project_directory.iterdir()):
            QMessageBox.warning(self, "Invalid Directory",
                                "The selected directory is not empty. Please select an empty directory, "
                                "or create a new one.")
            return
        return project_directory

    def save_project(self) -> bool:
        if not self._check_project():
            return False
        if not self._abs_project_directory:
            project_directory = self._browse_for_new_project_directory()
            if not project_directory:
                return False
            self._set_project_directory(project_directory)
        self._save_project()
        return True

    def _save_project(self):
        if self.is_locked:
            return
        config = self._convert_widgets_to_config()
        self.steps_runner_cls.create_project_directory_from_project_parameters(
            self._abs_project_directory, config)

    def _check_data_files_exist(self) -> bool:
        config = self._convert_widgets_to_config()
        try:
            self.steps_runner_cls.check_files_exist(self._abs_project_directory, config)
        except FileNotFoundError as e:
            QMessageBox.warning(self, "Missing Files",
                                f"Cannot start the project:\n{e}")
            return False
        return True

    """Open project"""

    @property
    def project_file_name(self):
        return self.steps_runner_cls.PROJECT_PARAMETERS_FILENAME

    def open_project(self, project_directory: Optional[Path] = None):
        if project_directory is None:
            project_directory = self._browse_for_existing_project_directory()
            if not project_directory:
                return
        self._set_project_directory(project_directory)
        project_directory = self._abs_project_directory
        config = self.steps_runner_cls.get_project_parameters_from_project_directory(project_directory,
                                                                                     add_default_parameters=False)
        self.current_config = config
        self._convert_config_to_widgets(config)
        runs_folder = project_directory / 'runs'
        is_previous_runs = runs_folder.exists() and bool(list(runs_folder.iterdir()))
        self._lock_project_for_editing(disable=is_previous_runs)

    def _convert_config_to_widgets(self, config):
        pass

    def _browse_for_existing_project_directory(self) -> Optional[Path]:
        project_directory = QFileDialog.getOpenFileName(
            self, "Select a data file", str(BASE_PROJECT_DIRECTORY),
            f"{self.project_file_name} ({self.project_file_name});;All Files (*)")[0]

        if not project_directory:
            return  # user cancelled
        project_directory = Path(project_directory).parent

        # check that the project directory contains the project parameters file:
        if not (project_directory / self.project_file_name).exists():
            QMessageBox.warning(self, "Invalid Directory",
                                "The selected directory is not a valid project directory. "
                                f"Please select a directory, containing '{self.project_file_name}'.")
            return
        return project_directory

    def _set_project_directory(self, project_directory: Optional[Path]):
        self._abs_project_directory = project_directory
        if project_directory is None:
            self.project_folder_label.setText('Untitled')
        else:
            try:
                project_directory = project_directory.relative_to(BASE_PROJECT_DIRECTORY)
            except ValueError:
                pass
            self.project_folder_label.setText(str(project_directory))

    """Start project"""

    def _convert_widgets_to_config(self) -> dict:
        config = self.current_config
        return config

    def get_project_parameters(self):
        return self._abs_project_directory, self._convert_widgets_to_config()

    def on_start_clicked(self):
        if not self._check_project():
            return
        if not self.save_project():
            return
        if not self._check_data_files_exist():
            return
        self.accept()


class DataFilesStartDialog(BaseStartDialog):

    def _get_date_files_widget(self):
        return self.widgets['files_widget']

    def _create_widgets(self):
        return {
            'files_widget': MultiFileWidget(),
        }

    def _convert_config_to_widgets(self, config):
        files_widget = self._get_date_files_widget()
        files_widget.clear(num_files=0)
        for file_path, is_binary, description in zip(
                config.get('data_filenames', []),
                config.get('data_files_is_binary', []),
                config.get('data_file_descriptions', [])):
            files_widget.add_file(file_path, is_binary, description)
        super()._convert_config_to_widgets(config)

    def _convert_widgets_to_config(self) -> dict:
        config = super()._convert_widgets_to_config()
        data_filenames = []
        data_file_descriptions = []
        data_files_is_binary = []
        for file_widget in self._get_date_files_widget().get_all_file_widgets():
            if file_widget.abs_path:
                data_filenames.append(file_widget.abs_or_rel_path)
                data_file_descriptions.append(file_widget.description)
                data_files_is_binary.append(file_widget.is_binary)
        config['data_filenames'] = data_filenames
        config['data_files_is_binary'] = data_files_is_binary
        config['data_file_descriptions'] = data_file_descriptions
        return config

    def _set_project_directory(self, project_directory: Optional[Path]):
        super()._set_project_directory(project_directory)
        self._get_date_files_widget().set_project_directory(project_directory)

    def _get_mandatory_items_to_start(self):
        raise NotImplementedError

    def update_start_button_state(self):
        mandatory_items = self._get_mandatory_items_to_start()

        # access the start_button from the layout
        start_button = self.layout.itemAt(self.layout.count() - 1).itemAt(0).widget()
        start_button.setDisabled(any(not item for item in mandatory_items))

    def open_project(self, project_directory: Optional[Path] = None):
        super().open_project(project_directory)
        self.update_start_button_state()


def interactively_create_project_folder(steps_runner_cls: Type[BaseStepsRunner],
                                        project_directory: Optional[Path] = None) -> Tuple[Path, dict]:
    get_or_create_q_application_if_app_is_pyside()
    start_dialog = steps_runner_cls.APP_STARTUP_CLS(
        steps_runner_cls=steps_runner_cls,
        project_directory=project_directory)
    if start_dialog.exec() == QDialog.Accepted:  # noqa
        pass
    else:
        sys.exit(0)
    return start_dialog.get_project_parameters()
