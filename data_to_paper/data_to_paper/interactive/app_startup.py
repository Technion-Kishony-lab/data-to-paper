import json
import os
import sys
from functools import partial
from pathlib import Path
from typing import List, Tuple

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QApplication, QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog,
                               QMessageBox, QTextEdit, QWidget, QHBoxLayout, QSizePolicy, QListWidget, QFrame)

from data_to_paper.interactive.get_app import get_or_create_app
from data_to_paper_examples.examples.run_project import get_paper

BASE_DIRECTORY = Path(__file__).parent

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


class StartDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.config_file = BASE_DIRECTORY / Path("config/run_setup.json")
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

        # Project list and buttons
        self.layout.addWidget(QLabel("Manage the projects you have already started:"))
        self.list_widget = QListWidget()
        self.list_widget.setFixedHeight(100)
        self.list_widget.setStyleSheet(text_box_style)
        self.layout.addWidget(self.list_widget)
        button_layout = QHBoxLayout()
        load_button = QPushButton("Load Project")
        load_button.setStyleSheet(positive_button_style)
        load_button.clicked.connect(self.on_load_clicked)
        button_layout.addWidget(load_button)
        delete_button = QPushButton("Delete Project")
        delete_button.setStyleSheet(negative_button_style)
        delete_button.clicked.connect(self.on_delete_clicked)
        button_layout.addWidget(delete_button)
        self.layout.addLayout(button_layout)

        # Project name input
        project_name_layout = QHBoxLayout()
        self.layout.addLayout(project_name_layout)
        project_name_layout.addWidget(QLabel("Project name:"))
        self.project_name_edit = QLineEdit()
        self.project_name_edit.setStyleSheet(text_box_style)
        self.project_name_edit.setPlaceholderText("Enter a unique project name")
        project_name_layout.addWidget(self.project_name_edit)

        # General description input with info label
        general_desc_layout = QVBoxLayout()
        general_desc_layout.addWidget(QLabel("Dataset description:"))
        self.general_description_edit = PlainTextPasteTextEdit()
        self.general_description_edit.setPlaceholderText("Describe the dataset, its origin, content, purpose, etc.")
        self.general_description_edit.setStyleSheet(text_box_style)
        general_desc_layout.addWidget(self.general_description_edit)
        self.layout.addLayout(general_desc_layout)

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
        research_goal_layout.addWidget(QLabel("Research goal:"))
        self.layout.addLayout(research_goal_layout)

        self.goal_edit = PlainTextPasteTextEdit()
        self.goal_edit.setStyleSheet(text_box_style)
        self.goal_edit.setFixedHeight(100)
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

        self.load_configurations()

    def save_configuration(self):
        # Read existing configs or initialize new dictionary
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as file:
                configs = json.load(file)
        else:
            configs = {}

        # Update current project's config
        project_name = self.project_name_edit.text().strip().lower().replace(' ', '_')
        if project_name:
            configs[project_name] = {
                'general_description': self.general_description_edit.toPlainText(),
                'goal': self.goal_edit.toPlainText(),
                'files': [],
                'descriptions': []
            }
            for i in range(self.files_layout.count()):
                file_widget = self.files_layout.itemAt(i).widget()
                _, file_edit, _, _, description_edit = self._get_widgets_from_file_widget(file_widget)
                configs[project_name]['files'].append(file_edit.text())
                configs[project_name]['descriptions'].append(description_edit.toPlainText())

            with open(self.config_file, 'w+') as file:
                json.dump(configs, file, indent=4)

    def load_configurations(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as file:
                configs = json.load(file)
            self.list_widget.clear()
            for project in configs:
                self.list_widget.addItem(project)

    def load_project(self, project_name):
        with open(self.config_file, 'r') as file:
            configs = json.load(file)
        config = configs.get(project_name, {})
        self.project_name_edit.setText(project_name)
        self.general_description_edit.setPlainText(config.get('general_description', ''))
        self.goal_edit.setPlainText(config.get('goal', ''))
        while self.files_layout.count():
            widget = self.files_layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()
        for file_path, description in zip(config.get('files', []), config.get('descriptions', [])):
            self.add_file_input(file_path, description)

        self.project_name_edit.setDisabled(True)
        self.general_description_edit.setDisabled(True)
        self.goal_edit.setDisabled(True)
        self.add_file_button.setDisabled(True)
        # Disable file inputs
        for i in range(self.files_layout.count()):
            file_widget = self.files_layout.itemAt(i).widget()
            if file_widget:
                _, file_edit, browse_button, delete_button, description_edit = self._get_widgets_from_file_widget(file_widget)
                file_edit.setDisabled(True)
                browse_button.setDisabled(True)
                description_edit.setDisabled(True)
                delete_button.setDisabled(True)

    def _get_widgets_from_file_widget(self, file_widget):
        layout = file_widget.layout()
        file_path_tray = layout.itemAt(0)
        label = file_path_tray.itemAt(1).widget()
        file_edit = file_path_tray.itemAt(2).widget()
        browse_button = file_path_tray.itemAt(3).widget()
        delete_button = file_path_tray.itemAt(4).widget()
        description_edit = layout.itemAt(1).widget()
        return label, file_edit, browse_button, delete_button, description_edit

    def delete_project(self, project_name):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as file:
                configs = json.load(file)
            if project_name in configs:
                del configs[project_name]
                with open(self.config_file, 'w') as file:
                    json.dump(configs, file, indent=4)
            self.load_configurations()

    def on_load_clicked(self):
        selected_item = self.list_widget.currentItem()
        if selected_item:
            self.load_project(selected_item.text())

    def on_delete_clicked(self):
        selected_item = self.list_widget.currentItem()
        if selected_item:
            reply = QMessageBox.question(self, 'Confirm Delete',
                                         f"Are you sure you want to delete the project '{selected_item.text()}'?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.delete_project(selected_item.text())
            else:
                # If the user decides not to delete, do nothing
                return

    def add_file_input(self, file_path='', description=''):
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

        browse_button = QPushButton("Browse")
        browse_button.setStyleSheet(positive_button_style)
        browse_button.clicked.connect(partial(self.browse_files, file_edit))
        file_path_tray.addWidget(browse_button)

        file_input_layout.addLayout(file_path_tray)

        description_edit = PlainTextPasteTextEdit()
        description_edit.setPlaceholderText("Enter file description here...")
        description_edit.setStyleSheet(text_box_style)
        description_edit.setPlainText(description)
        file_input_layout.addWidget(description_edit)

        remove_button = QPushButton("Delete")
        remove_button.setStyleSheet(negative_button_style)
        remove_button.clicked.connect(partial(self.remove_file_input, file_input_widget))
        file_path_tray.addWidget(remove_button)

        # Set frame shape and add spacing around the frame
        file_input_widget.setFrameShape(QFrame.Box)
        file_input_widget.setFrameShadow(QFrame.Plain)
        file_input_layout.setContentsMargins(5, 5, 5, 5)

        self.files_layout.addWidget(file_input_widget)

    def remove_file_input(self, widget):
        widget.destroyed.connect(self.update_file_labels)
        widget.deleteLater()

    def update_file_labels(self):
        print("Updating file labels, count:", self.files_layout.count())
        i = 0
        num = 1
        while True:
            try:
                file_widget = self.files_layout.itemAt(i).widget()
            except Exception:
                break
            if file_widget and file_widget.layout():
                label, _, _, _, _ = self._get_widgets_from_file_widget(file_widget)
                label.setText(f"File path for file {num}:")
                num += 1
            i += 1

    def close_app(self):
        self.reject()
        QApplication.instance().exit()  # Exit the application

    def browse_files(self, file_edit):
        file, _ = QFileDialog.getOpenFileName(self, "Select a data file", "",
                                              "CSV Files (*.csv);;ZIP Files (*.zip);;All Files (*)")
        if file:
            file_edit.setText(file)

    def _get_file_paths_and_descriptions(self) -> List[Tuple[str, str]]:
        file_paths_and_descriptions = []
        for i in range(self.files_layout.count()):
            file_widget = self.files_layout.itemAt(i).widget()
            if file_widget:
                label, file_edit, browse_button, delete_button, description_edit = self._get_widgets_from_file_widget(file_widget)
                file_paths_and_descriptions.append((file_edit.text(), description_edit.toPlainText()))
        return file_paths_and_descriptions

    def get_project_details(self):
        project_name = self.project_name_edit.text()
        general_description = self.general_description_edit.toPlainText()
        files = []
        descriptions = []
        for file_path, description in self._get_file_paths_and_descriptions():
            if file_path and description:
                files.append(file_path)
                descriptions.append(description)

        goal = self.goal_edit.toPlainText()
        return project_name, general_description, goal, files, descriptions

    def on_start_clicked(self):
        project_name, general_description, goal, file_paths, descriptions = self.get_project_details()
        if (project_name and general_description and file_paths and descriptions and
                len(file_paths) == len(descriptions)):
            # check the files exist
            for file_path in file_paths:
                if not os.path.exists(file_path):
                    QMessageBox.warning(self, "File Not Found",
                                        f"File '{file_path}' does not exist. "
                                        "You might have provided an incorrect file path or moved the file."
                                        f"Please provide a valid file path.")
                    return
            self.save_configuration()
            self.accept()
        else:
            QMessageBox.warning(self, "Input Required",
                                "Please provide a project name, general description and provide at least one file "
                                "with its description.")


def run_app():
    app = QApplication(sys.argv)  # Create QApplication once
    while True:
        start_dialog = StartDialog()
        if start_dialog.exec() == QDialog.Accepted:
            project_name, general_description, goal, file_paths, descriptions = start_dialog.get_project_details()
            project_name = project_name.strip().lower().replace(' ', '_')
            file_names = [path.split('/')[-1] for path in file_paths]
            RUN_PARAMETERS = {
                'project': project_name,
                'research_goal': goal if goal else None,
                'general_description': general_description,
                'data_file_paths': file_paths,
                'data_filenames': file_names,
                'file_descriptions': descriptions,
                'output_folder': project_name + '_run'
            }
            break
        else:
            sys.exit(0)

    main_app = get_or_create_app(app)  # Pass the existing QApplication instance
    main_app.start_worker(partial(get_paper, **RUN_PARAMETERS))
    sys.exit(app.exec())


if __name__ == '__main__':
    run_app()
