import sys
from functools import partial
from pathlib import Path
from typing import List, Tuple, NamedTuple, Type, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, \
    QMessageBox, QTextEdit, QWidget, QHBoxLayout, QSizePolicy, QFrame, QCheckBox

from data_to_paper.base_products.file_descriptions import TEXT_EXTS
from data_to_paper.base_steps import BaseStepsRunner
from data_to_paper.env import BASE_FOLDER
from data_to_paper.interactive.get_app import get_or_create_q_application_if_app_is_pyside

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

QLineEdit {
    height: 25px; /* Adjust the height here */
    padding: 5px 10px;
}
"""


text_box_style = "background-color: #151515; color: white;"


class PlainTextPasteTextEdit(QTextEdit):
    def insertFromMimeData(self, source):
        if source.hasText():
            # Insert text as plain text, removing any formatting
            self.insertPlainText(source.text())
        else:
            super().insertFromMimeData(source)  # Default behavior for non-text data if needed


def create_info_label(tooltip_text):
    info_label = QLabel("ℹ️")
    info_label.setToolTip(tooltip_text)
    info_label.setStyleSheet("font-size: 14pt; color: white;")
    return info_label


class FileDialogProperties(NamedTuple):
    label: QLabel
    path: QLineEdit
    is_binary: QCheckBox
    browse: QPushButton
    delete: QPushButton
    description: QTextEdit


class StartDialog(QDialog):
    def __init__(self, steps_runner_cls: Type[BaseStepsRunner] = None,
                 project_directory: Optional[Path] = None):
        super().__init__()
        self.steps_runner_cls = steps_runner_cls
        self.current_config = {}
        self.is_locked = False

        self._set_style()

        self.layout = QVBoxLayout(self)
        self.layout.addLayout(self._get_project_name_layout())
        self.layout.addLayout(self._get_general_description_layout())
        self.layout.addLayout(self._add_file_layout())
        self.layout.addLayout(self._add_research_goal_layout())
        self.layout.addLayout(self._add_start_exist_buttons_layout())
        self._initialize(project_directory)

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

    def _get_project_name_layout(self):
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

    def _get_general_description_layout(self):
        general_desc_layout = QVBoxLayout()
        general_desc_layout.addWidget(QLabel("Dataset description:"))
        self.general_description_edit = PlainTextPasteTextEdit()
        self.general_description_edit.setPlaceholderText("Describe the dataset, its origin, content, purpose, etc.")
        self.general_description_edit.setStyleSheet(text_box_style)
        general_desc_layout.addWidget(self.general_description_edit)
        return general_desc_layout

    def _add_file_layout(self):
        full_files_layout = QVBoxLayout()
        self.files_layout = QVBoxLayout()
        full_files_layout.addLayout(self.files_layout)
        self.add_file_button = QPushButton("Add Another File")
        self.add_file_button.clicked.connect(self.add_data_file)
        self.add_file_button.setFixedWidth(200)  # prevent button from expanding
        full_files_layout.addWidget(self.add_file_button, alignment=Qt.AlignHCenter)  # center it in the layout
        self.add_data_file()
        return full_files_layout

    def _add_research_goal_layout(self):
        research_goal_layout = QVBoxLayout()
        self.layout.addLayout(research_goal_layout)
        research_goal_layout.addWidget(QLabel("Research goal:"))
        self.goal_edit = PlainTextPasteTextEdit()
        self.goal_edit.setStyleSheet(text_box_style)
        self.goal_edit.setPlaceholderText(
            "Optionally specify the research goal, or leave blank for autonomous goal setting.")
        research_goal_layout.addWidget(self.goal_edit)
        return research_goal_layout

    def _add_start_exist_buttons_layout(self):
        buttons_tray = QHBoxLayout()
        start_button = QPushButton("Save and Start")
        start_button.clicked.connect(self.on_start_clicked)
        buttons_tray.addWidget(start_button)

        close_button = QPushButton("Exit")
        close_button.clicked.connect(self.close_app)
        buttons_tray.addWidget(close_button)
        return buttons_tray

    def _delete_all_data_file_widgets(self):
        while self.files_layout.count():
            widget = self.files_layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()

    def _clear_all(self):
        self._set_project_directory(None)
        self.general_description_edit.clear()
        self.goal_edit.clear()
        self._delete_all_data_file_widgets()
        self._lock_project_for_editing(disable=False)
        self.add_data_file()
        self.current_config = {}

    def close_app(self):
        self.reject()
        QApplication.instance().exit()  # Exit the application

    def _lock_project_for_editing(self, disable=True):
        self.is_locked = disable
        self.project_folder_header.setText("Project [LOCKED]:" if disable else "Project:")
        self.general_description_edit.setReadOnly(disable)
        self.goal_edit.setReadOnly(disable)
        self.add_file_button.setDisabled(disable)
        self.save_button.setDisabled(disable)
        # Disable file inputs
        for i in range(self.files_layout.count()):
            file_widget = self.files_layout.itemAt(i).widget()
            if file_widget:
                file_widget = self._get_widgets_from_file_widget(file_widget)
                file_widget.path.setDisabled(disable)
                file_widget.is_binary.setDisabled(disable)
                file_widget.browse.setDisabled(disable)
                file_widget.delete.setDisabled(disable)
                file_widget.description.setReadOnly(disable)

    """Data files input"""

    def _get_widgets_from_file_widget(self, file_widget) -> FileDialogProperties:
        layout = file_widget.layout()
        file_path_tray = layout.itemAt(0)
        label = file_path_tray.itemAt(1).widget()
        file_edit = file_path_tray.itemAt(2).widget()
        is_binary_checkbox = file_path_tray.itemAt(3).widget()
        browse_button = file_path_tray.itemAt(4).widget()
        delete_button = file_path_tray.itemAt(5).widget()
        description_edit = layout.itemAt(1).widget()
        return \
            FileDialogProperties(label, file_edit, is_binary_checkbox, browse_button, delete_button, description_edit)

    def _get_all_data_file_widgets(self) -> List[FileDialogProperties]:
        file_widgets = []
        for i in range(self.files_layout.count()):
            file_widget = self.files_layout.itemAt(i).widget()
            if file_widget and file_widget.layout():
                file_widgets.append(self._get_widgets_from_file_widget(file_widget))
        return file_widgets

    def add_data_file(self, file_path='', is_binary=False, description=''):
        file_input_widget = QFrame()  # Create a QFrame for encapsulating the file input widget
        file_input_layout = QVBoxLayout(file_input_widget)  # Maintain horizontal layout

        # Dynamic label for file input
        file_path_tray = QHBoxLayout()

        description_info = create_info_label(
            "Add a data file by clicking the 'Browse' button.\n"
            "Provide a description of the file, including the type of data and attribute names.")
        file_path_tray.addWidget(description_info)

        file_count = self.files_layout.count()  # This counts current file inputs
        file_label = QLabel(f"File #{file_count + 1}:")
        file_path_tray.addWidget(file_label)

        file_edit = QLineEdit()
        file_edit.setReadOnly(True)
        file_edit.setStyleSheet(text_box_style)
        file_edit.setText(file_path)
        file_path_tray.addWidget(file_edit)

        is_binary_checkbox = QCheckBox("Binary")
        is_binary_checkbox.setChecked(is_binary)
        file_path_tray.addWidget(is_binary_checkbox)

        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(partial(self.browse_data_files, file_edit, is_binary_checkbox))
        file_path_tray.addWidget(browse_button)

        remove_button = QPushButton("Delete")
        remove_button.clicked.connect(partial(self._remove_data_file, file_input_widget))
        file_path_tray.addWidget(remove_button)

        file_input_layout.addLayout(file_path_tray)

        description_edit = PlainTextPasteTextEdit()
        description_edit.setPlaceholderText("Enter file description here...")
        description_edit.setStyleSheet(text_box_style)
        description_edit.setPlainText(description)
        file_input_layout.addWidget(description_edit)

        # Set frame shape and add spacing around the frame
        file_input_widget.setFrameShape(QFrame.Box)
        file_input_widget.setFrameShadow(QFrame.Plain)
        file_input_layout.setContentsMargins(5, 5, 5, 5)

        self.files_layout.addWidget(file_input_widget)

    def _remove_data_file(self, widget):
        widget.destroyed.connect(self._update_data_file_labels)
        widget.deleteLater()

    def _update_data_file_labels(self):
        for index, file_widget in enumerate(self._get_all_data_file_widgets()):
            file_widget.label.setText(f"File #{index + 1}:")

    def browse_data_files(self, file_edit, is_binary_checkbox):
        project_directory = self._get_absolute_project_directory()
        search_in = str(BASE_PROJECT_DIRECTORY) if project_directory is None else str(project_directory)
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select a data file", search_in,
            "CSV Files (*.csv);;TEXT Files (*.txt);;Excel Files (*.xlsx, *.xls);;ZIP Files (*.zip);;All Files (*)")
        if file_path:
            file_path = file_path.replace('.zip', '')
            file_path = self._convert_abs_data_file_path_to_abs_or_rel(file_path)
            file_edit.setText(file_path)
            ext = file_path.split('.')[-1]
            is_binary = '.' + ext not in TEXT_EXTS
            is_binary_checkbox.setChecked(is_binary)

    def _convert_abs_data_file_path_to_abs_or_rel(self, data_file_path: str) -> str:
        if not data_file_path:
            return ''
        project_directory = self._get_absolute_project_directory()
        data_file_path = Path(data_file_path)
        if project_directory is not None:
            try:
                data_file_path = get_relative_path(project_directory, data_file_path)
            except ValueError:
                pass
        return str(data_file_path)

    def _convert_abs_or_rel_data_file_path_to_abs(self, data_file_path: str) -> str:
        if not data_file_path:
            return ''
        project_directory = self._get_absolute_project_directory()
        data_file_path = Path(data_file_path)
        if not data_file_path.is_absolute() and project_directory is not None:
            data_file_path = project_directory / data_file_path
        return str(data_file_path)

    """Save project"""

    def _check_project(self) -> bool:
        project_name, config = self.get_project_parameters()
        return True

    def _browse_for_new_project_directory(self) -> Optional[Path]:
        dialog = QFileDialog(self, "Save Project: Select or create an empty directory",
                             str(BASE_PROJECT_DIRECTORY))
        dialog.setFileMode(QFileDialog.Directory)
        dialog.setOption(QFileDialog.ShowDirsOnly, True)
        dialog.setAcceptMode(QFileDialog.AcceptOpen)
        if dialog.exec() != QFileDialog.Accepted:
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
        if not self._get_absolute_project_directory():
            project_directory = self._browse_for_new_project_directory()
            if not project_directory:
                return False
            self._set_project_directory(project_directory)
        self._save_project()
        return True

    def _save_project(self):
        if self.is_locked:
            return
        project_directory, config = self.get_project_parameters()
        self.steps_runner_cls.create_project_directory_from_project_parameters(
            project_directory, config)

    def _check_data_files_exist(self) -> bool:
        project_directory, config = self.get_project_parameters()
        try:
            self.steps_runner_cls.check_files_exist(project_directory, config)
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
        project_directory = self._get_absolute_project_directory()
        config = self.steps_runner_cls.get_project_parameters_from_project_directory(project_directory,
                                                                                     add_default_parameters=False)
        self.current_config = config
        self.general_description_edit.setPlainText(config.get('general_description', ''))
        self.goal_edit.setPlainText(config.get('research_goal', '') or '')
        self._delete_all_data_file_widgets()
        for file_path, is_binary, description in zip(
                config.get('data_filenames', []),
                config.get('data_files_is_binary', []),
                config.get('data_file_descriptions', [])):
            self.add_data_file(file_path, is_binary, description)

        run_folder = project_directory / 'runs'
        self._lock_project_for_editing(disable=run_folder.exists())

    def _browse_for_existing_project_directory(self) -> Optional[Path]:
        # project_directory = QFileDialog.getExistingDirectory(self, "Select a project directory",
        #                                                      str(BASE_PROJECT_DIRECTORY))
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
        # first, get all the data file abs paths:
        data_file_widgets = self._get_all_data_file_widgets()
        abs_data_file_paths = [self._convert_abs_or_rel_data_file_path_to_abs(file_widget.path.text())
                               for file_widget in data_file_widgets]
        if project_directory is None:
            self.project_folder_label.setText('Untitled')
        else:
            try:
                project_directory = project_directory.relative_to(BASE_PROJECT_DIRECTORY)
            except ValueError:
                pass
            self.project_folder_label.setText(str(project_directory))
            for abs_data_file_path, file_widget in zip(abs_data_file_paths, data_file_widgets):
                file_widget.path.setText(self._convert_abs_data_file_path_to_abs_or_rel(abs_data_file_path))

    def _get_absolute_project_directory(self):
        project_directory = self.project_folder_label.text()
        if not project_directory or project_directory == 'Untitled':
            return
        project_directory = Path(project_directory)
        if not project_directory.is_absolute():
            project_directory = BASE_PROJECT_DIRECTORY / project_directory
        return project_directory

    """Start project"""

    def get_project_parameters(self) -> Tuple[Path, dict]:
        config = self.current_config
        project_directory = self._get_absolute_project_directory()
        config['general_description'] = self.general_description_edit.toPlainText()
        data_filenames = []
        data_file_descriptions = []
        data_files_is_binary = []
        for file_widget in self._get_all_data_file_widgets():
            if file_widget.path.text():
                data_filenames.append(file_widget.path.text())
                data_file_descriptions.append(file_widget.description.toPlainText())
                data_files_is_binary.append(file_widget.is_binary.isChecked())
        config['data_filenames'] = data_filenames
        config['data_files_is_binary'] = data_files_is_binary
        config['data_file_descriptions'] = data_file_descriptions
        config['research_goal'] = self.goal_edit.toPlainText() or None
        return project_directory, config

    def on_start_clicked(self):
        if not self._check_project():
            return
        if not self.save_project():
            return
        if not self._check_data_files_exist():
            return
        self.accept()


def interactively_create_project_folder(steps_runner_cls: Type[BaseStepsRunner],
                                        project_directory: Optional[Path] = None) -> Tuple[Path, dict]:
    get_or_create_q_application_if_app_is_pyside()
    start_dialog = StartDialog(steps_runner_cls=steps_runner_cls, project_directory=project_directory)
    if start_dialog.exec() == QDialog.Accepted:
        pass
    else:
        sys.exit(0)
    return start_dialog.get_project_parameters()
