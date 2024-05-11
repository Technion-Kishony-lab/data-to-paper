import os
import sys
from functools import partial
from pathlib import Path
from typing import List, Tuple, NamedTuple, Type

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QApplication, QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog,
                               QMessageBox, QTextEdit, QWidget, QHBoxLayout, QSizePolicy, QListWidget, QFrame,
                               QCheckBox)

from data_to_paper.base_products.file_descriptions import TEXT_EXTS
from data_to_paper.base_steps import BaseStepsRunner
from data_to_paper.env import BASE_FOLDER
from data_to_paper.research_types.scientific_research.steps_runner import ScientificStepsRunner
from data_to_paper.run.run_all_steps import run_all_steps
from data_to_paper.utils.file_utils import is_valid_filename

BASE_PROJECT_DIRECTORY = BASE_FOLDER / 'projects'


STEPS_RUNNER_CLS = ScientificStepsRunner

style_sheet = """
QWidget {
    background-color: #404040; /* Application Background Color */
    color: white;
    font-family: Arial, Arial;
    font-size: 14pt;
}

QPushButton {
    background-color: #606060; /* Dark Grey */
    border: none;
    color: #ffffff; /* White */
    padding: 10px 24px;
    text-align: center;
    text-decoration: none;
    font-size: 16px;
    margin: 4px 2px;
    border-radius: 12px;
    height: 12px;
}

QPushButton:hover {
    background-color: #808080; /* Lighter Grey */
}

QPushButton:pressed {
    background-color: #404040; /* Darker Grey */
}

QLineEdit {
    height: 25px; /* Adjust the height here */
    padding: 5px 10px;
}
"""


text_box_style = "background-color: #151515; color: white;"

# no border for buttons:
negative_button_style = "background-color: #aa6060;"
positive_button_style = "background-color: #60aa60;"


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
    def __init__(self, steps_runner_cls: Type[BaseStepsRunner] = None):
        super().__init__()
        self.steps_runner_cls = steps_runner_cls
        self.current_config = {}
        self.setWindowTitle("data-to-paper: Set Project Details")
        self.resize(1000, 1000)

        self.setStyleSheet(style_sheet)

        self.layout = QVBoxLayout(self)

        # Top bar layout for close button
        top_bar_layout = QHBoxLayout()
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        top_bar_layout.addWidget(spacer)
        close_button = QPushButton("Exit")
        close_button.setStyleSheet(negative_button_style)
        close_button.clicked.connect(self.close_app)
        self.layout.addLayout(top_bar_layout)

        # Project name input
        project_name_layout = QHBoxLayout()
        self.layout.addLayout(project_name_layout)
        project_name_layout.addWidget(QLabel("Project:"))
        self.project_folder_edit = QLineEdit()
        self.project_folder_edit.setStyleSheet(text_box_style)
        self.project_folder_edit.setPlaceholderText("Enter the project folder")
        project_name_layout.addWidget(self.project_folder_edit)
        load_button = QPushButton("Load")
        load_button.setStyleSheet(positive_button_style)
        load_button.clicked.connect(self.browse_project)
        project_name_layout.addWidget(load_button)
        new_button = QPushButton("New")
        new_button.setStyleSheet(negative_button_style)
        new_button.clicked.connect(self._clear_all)
        project_name_layout.addWidget(new_button)

        # General description input with info label
        general_desc_layout = QVBoxLayout()
        self.layout.addLayout(general_desc_layout)
        general_desc_layout.addWidget(QLabel("Dataset description:"))
        self.general_description_edit = PlainTextPasteTextEdit()
        self.general_description_edit.setPlaceholderText("Describe the dataset, its origin, content, purpose, etc.")
        self.general_description_edit.setStyleSheet(text_box_style)
        general_desc_layout.addWidget(self.general_description_edit)

        # File inputs and descriptions
        self.files_layout = QVBoxLayout()
        self.layout.addLayout(self.files_layout)
        self.add_file_button = QPushButton("Add Another File")
        self.add_file_button.setStyleSheet(positive_button_style)
        self.add_file_button.clicked.connect(self.add_file_input)
        # Set fixed width to prevent button from expanding and center it in the layout
        self.add_file_button.setFixedWidth(200)
        self.layout.addWidget(self.add_file_button, alignment=Qt.AlignHCenter)
        self.add_file_input()

        # Research goal input with info label
        research_goal_layout = QVBoxLayout()
        self.layout.addLayout(research_goal_layout)
        research_goal_layout.addWidget(QLabel("Research goal:"))
        self.goal_edit = PlainTextPasteTextEdit()
        self.goal_edit.setStyleSheet(text_box_style)
        self.goal_edit.setPlaceholderText(
            "Optionally specify the research goal, or leave blank for autonomous goal setting.")
        research_goal_layout.addWidget(self.goal_edit)

        # Start button
        start_button = QPushButton("Start Project")
        start_button.setStyleSheet(positive_button_style)
        start_button.clicked.connect(self.on_start_clicked)

        # Buttons tray:
        buttons_tray = QHBoxLayout()
        buttons_tray.addWidget(start_button)
        buttons_tray.addWidget(close_button)
        self.layout.addLayout(buttons_tray)

    def _delete_all_file_widgets(self):
        while self.files_layout.count():
            widget = self.files_layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()

    def _clear_all(self):
        self.project_folder_edit.clear()
        self.general_description_edit.clear()
        self.goal_edit.clear()
        self._delete_all_file_widgets()
        self.add_file_input()

    def load_project(self, project_directory: str):
        project_directory = Path(project_directory)

        # if the project directory is under the base project directory, remove the base project directory:
        if project_directory.parts[:len(BASE_PROJECT_DIRECTORY.parts)] == BASE_PROJECT_DIRECTORY.parts:
            project_directory = project_directory.relative_to(BASE_PROJECT_DIRECTORY)
        # path:
        self.project_folder_edit.setText(str(project_directory))
        config = self.steps_runner_cls.get_project_parameters_from_project_directory(project_directory)
        self.general_description_edit.setPlainText(config.get('general_description', ''))
        self.goal_edit.setPlainText(config.get('research_goal', ''))
        self._delete_all_file_widgets()
        for file_path, is_binary, description in zip(
                config.get('data_filenames', []),
                config.get('data_files_is_binary', []),
                config.get('data_file_descriptions', [])):
            self.add_file_input(file_path, is_binary, description)

        run_folder = project_directory / 'runs'
        if run_folder.exists():
            self._disable_inputs()

    def _disable_inputs(self):
        self.project_folder_edit.setDisabled(True)
        self.general_description_edit.setDisabled(True)
        self.goal_edit.setDisabled(True)
        self.add_file_button.setDisabled(True)
        # Disable file inputs
        for i in range(self.files_layout.count()):
            file_widget = self.files_layout.itemAt(i).widget()
            if file_widget:
                _, file_edit, is_binary_checkbox, browse_button, delete_button, description_edit = \
                    self._get_widgets_from_file_widget(file_widget)
                file_edit.setDisabled(True)
                is_binary_checkbox.setDisabled(True)
                browse_button.setDisabled(True)
                description_edit.setDisabled(True)
                delete_button.setDisabled(True)

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

    def _get_all_file_widgets(self) -> List[FileDialogProperties]:
        file_widgets = []
        for i in range(self.files_layout.count()):
            file_widget = self.files_layout.itemAt(i).widget()
            if file_widget and file_widget.layout():
                file_widgets.append(self._get_widgets_from_file_widget(file_widget))
        return file_widgets

    def add_file_input(self, file_path='', is_binary=False, description=''):
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
        browse_button.setStyleSheet(positive_button_style)
        browse_button.clicked.connect(partial(self.browse_files, file_edit, is_binary_checkbox))
        file_path_tray.addWidget(browse_button)

        remove_button = QPushButton("Delete")
        remove_button.setStyleSheet(negative_button_style)
        remove_button.clicked.connect(partial(self.remove_file_input, file_input_widget))
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

    def remove_file_input(self, widget):
        widget.destroyed.connect(self.update_file_labels)
        widget.deleteLater()

    def update_file_labels(self):
        for index, file_widget in enumerate(self._get_all_file_widgets()):
            file_widget.label.setText(f"File #{index + 1}:")

    def close_app(self):
        self.reject()
        QApplication.instance().exit()  # Exit the application

    def browse_files(self, file_edit, is_binary_checkbox):
        file, _ = QFileDialog.getOpenFileName(self, "Select a data file", "",
                                              "CSV Files (*.csv);;ZIP Files (*.zip);;All Files (*)")
        if file:
            file_edit.setText(file)
            file_name = Path(file).name.replace('.zip', '')
            ext = file_name.split('.')[-1]
            is_binary = ext not in TEXT_EXTS
            is_binary_checkbox.setChecked(is_binary)

    def browse_project(self):
        project_directory = QFileDialog.getExistingDirectory(self, "Select a project directory",
                                                             str(BASE_PROJECT_DIRECTORY))
        # check that project directory is a valid directory (contains data-to-paper.json)
        if not project_directory:
            return
        filename = self.steps_runner_cls.PROJECT_PARAMETERS_FILENAME
        if not (Path(project_directory) / filename).exists():
            QMessageBox.warning(self, "Invalid Directory",
                                "The selected directory is not a valid project directory. "
                                f"Please select a directory, containing '{filename}'.")
            return
        self.load_project(project_directory)

    def get_project_parameters(self):
        config = {}
        project_folder = self.project_folder_edit.text()
        config['general_description'] = self.general_description_edit.toPlainText()
        data_filenames = []
        data_file_descriptions = []
        data_files_is_binary = []
        for file_widget in self._get_all_file_widgets():
            if file_widget.path.text():
                data_filenames.append(file_widget.path.text())
                data_file_descriptions.append(file_widget.description.toPlainText())
                data_files_is_binary.append(file_widget.is_binary.isChecked())
        config['data_filenames'] = data_filenames
        config['data_files_is_binary'] = data_files_is_binary
        config['data_file_descriptions'] = data_file_descriptions
        config['research_goal'] = self.goal_edit.toPlainText()
        return project_folder, config

    def on_start_clicked(self):
        project_name, config = self.get_project_parameters()
        # check that project name is a valid file name
        if not project_name or not is_valid_filename(project_name):
            QMessageBox.warning(self, "Input Required", "Project name must be an alphanumeric string.")
            return
        if not config['general_description']:
            QMessageBox.warning(self, "Input Required", "Please provide a general description.")
            return
        # check the files exist
        for file_path in config['data_filenames']:
            if not os.path.exists(file_path):
                QMessageBox.warning(self, "File Not Found",
                                    f"File '{file_path}' does not exist. Please provide a valid file path.")
                return
        self.accept()


def interactively_get_project_parameters(steps_runner_cls: Type[BaseStepsRunner]) -> Tuple[Path, dict]:
    start_dialog = StartDialog(steps_runner_cls=steps_runner_cls)
    if start_dialog.exec() == QDialog.Accepted:
        pass
    else:
        sys.exit(0)
    project_folder, config = start_dialog.get_project_parameters()
    # resolve the project folder to a full path:
    # check if relative path is given:
    project_folder = Path(project_folder)
    if not project_folder.is_absolute():
        project_folder = BASE_PROJECT_DIRECTORY / project_folder
    return project_folder, config


def interactively_create_project_folder(steps_runner_cls: Type[BaseStepsRunner]) -> Tuple[Path, dict]:
    project_folder, config = interactively_get_project_parameters(steps_runner_cls)
    steps_runner_cls.create_project_directory_from_project_parameters(project_folder, config)
    return project_folder, config


def run_app(steps_runner_cls: Type[BaseStepsRunner],
            project_directory: Path = None,
            run_folder: str = 'run_001'):
    app = QApplication(sys.argv)  # Create QApplication once
    if not project_directory:
        project_directory, config = interactively_create_project_folder(steps_runner_cls)
    step_runner = steps_runner_cls(
        project_directory=project_directory,
        output_directory=project_directory / 'runs' / run_folder,
    )
    run_all_steps(step_runner=step_runner, q_application=app)  # Pass the existing QApplication instance


if __name__ == '__main__':
    run_app(STEPS_RUNNER_CLS, project_directory=None)
