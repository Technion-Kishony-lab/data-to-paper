import json
import os
import sys
from functools import partial
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QApplication, QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog,
                               QMessageBox, QTextEdit, QWidget, QHBoxLayout, QSizePolicy, QListWidget, QFrame)

from data_to_paper.interactive.get_app import get_or_create_app
from data_to_paper_examples.examples.run_project import get_paper

BASE_DIRECTORY = Path(__file__).parent


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


def create_horizontal_line():
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setFrameShadow(QFrame.Sunken)
    line.setStyleSheet("background-color: #858585;")
    line.setFixedHeight(2)
    return line


class StartDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.config_file = BASE_DIRECTORY / Path("config/run_setup.json")
        self.current_config = {}
        self.setWindowTitle("Set Project Details")
        self.setStyleSheet("background-color: #303030; color: white; font-family: Arial, sans-serif; font-size: 14pt;")
        self.resize(1000, 1000)

        self.layout = QVBoxLayout(self)

        # Top bar layout for close button
        top_bar_layout = QHBoxLayout()
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        top_bar_layout.addWidget(spacer)
        close_button = QPushButton("Exit")
        close_button.clicked.connect(self.close_app)
        top_bar_layout.addWidget(close_button)
        self.layout.addLayout(top_bar_layout)

        # Project list and buttons
        self.layout.addWidget(QLabel("Manage the projects you have already started:"))
        self.list_widget = QListWidget()
        self.list_widget.setFixedHeight(100)
        self.list_widget.setStyleSheet("background-color: #151515; color: white;")
        self.layout.addWidget(self.list_widget)
        button_layout = QHBoxLayout()
        load_button = QPushButton("Load Project")
        load_button.clicked.connect(self.on_load_clicked)
        button_layout.addWidget(load_button)
        delete_button = QPushButton("Delete Project")
        delete_button.clicked.connect(self.on_delete_clicked)
        button_layout.addWidget(delete_button)
        self.layout.addLayout(button_layout)

        self.layout.addWidget(create_horizontal_line())

        # Project name input
        self.layout.addWidget(QLabel("Enter the project name:"))
        self.project_name_edit = QLineEdit()
        self.project_name_edit.setStyleSheet("background-color: #151515; color: white;")
        self.layout.addWidget(self.project_name_edit)

        # General description input with info label
        general_desc_layout = QHBoxLayout()
        general_desc_layout.addWidget(QLabel("Enter the general description of the dataset:"))
        general_desc_info = create_info_label(
            "Include comprehensive details about the dataset's origin, contents, and any important metadata.")
        general_desc_layout.addWidget(general_desc_info)
        self.layout.addLayout(general_desc_layout)

        self.general_description_edit = PlainTextPasteTextEdit()
        self.general_description_edit.setStyleSheet("background-color: #151515; color: white;")
        self.layout.addWidget(self.general_description_edit)

        # File inputs and descriptions
        self.files_layout = QVBoxLayout()
        self.layout.addLayout(self.files_layout)
        self.add_file_button = QPushButton("Add Another File")
        self.add_file_button.clicked.connect(self.add_file_input)
        # Set fixed width to prevent button from expanding and center it in the layout
        self.add_file_button.setFixedWidth(200)
        self.layout.addWidget(self.add_file_button, alignment=Qt.AlignHCenter)
        self.add_file_input()

        # Research goal input with info label
        research_goal_layout = QHBoxLayout()
        research_goal_layout.addWidget(QLabel("Enter your research goal:"))
        research_goal_info = create_info_label(
            "Specify the objectives of your research clearly. Example: 'Determine the impact of A on B under conditions"
            " C and D.'")
        research_goal_layout.addWidget(research_goal_info)
        self.layout.addLayout(research_goal_layout)

        self.goal_edit = PlainTextPasteTextEdit()
        self.goal_edit.setStyleSheet("background-color: #151515; color: white;")
        self.goal_edit.setFixedHeight(100)
        self.goal_edit.setPlaceholderText("optional, if you won't provide it, data-to-paper will devise it for you!")
        self.layout.addWidget(self.goal_edit)

        self.layout.addWidget(create_horizontal_line())

        # Start button
        start_button = QPushButton("Start Project")
        start_button.clicked.connect(self.on_start_clicked)
        self.layout.addWidget(start_button)

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
                layout = file_widget.layout()
                file_edit = layout.itemAt(1).widget()
                description_edit = layout.itemAt(3).widget()
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
            self.add_file_input()
            file_widget = self.files_layout.itemAt(self.files_layout.count() - 1).widget()
            layout = file_widget.layout()
            file_edit = layout.itemAt(1).widget()
            description_edit = layout.itemAt(3).widget()
            file_edit.setText(file_path)
            description_edit.setPlainText(description)

        self.project_name_edit.setDisabled(True)
        self.general_description_edit.setDisabled(True)
        self.goal_edit.setDisabled(True)
        self.add_file_button.setDisabled(True)
        # Disable file inputs
        for i in range(self.files_layout.count()):
            file_widget = self.files_layout.itemAt(i).widget()
            if file_widget:
                layout = file_widget.layout()
                file_edit = layout.itemAt(1).widget()
                browse_button = layout.itemAt(2).widget()
                description_edit = layout.itemAt(3).widget()
                delete_button = layout.itemAt(5).widget()
                file_edit.setDisabled(True)
                browse_button.setDisabled(True)
                description_edit.setDisabled(True)
                delete_button.setDisabled(True)

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

    def add_file_input(self):
        file_input_widget = QWidget()
        file_input_layout = QHBoxLayout(file_input_widget)  # Maintain horizontal layout

        # Dynamic label for file input
        file_count = self.files_layout.count()  # This counts current file inputs
        file_label = QLabel(f"File path for file {file_count + 1}:")
        file_input_layout.addWidget(file_label)

        file_edit = QLineEdit()
        file_edit.setReadOnly(True)
        file_edit.setStyleSheet("background-color: #151515; color: white;")
        file_input_layout.addWidget(file_edit)

        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(partial(self.browse_files, file_edit))
        file_input_layout.addWidget(browse_button)

        description_edit = PlainTextPasteTextEdit()
        description_edit.setPlaceholderText("Enter file description here...")
        description_edit.setStyleSheet("background-color: #151515; color: white;")
        file_input_layout.addWidget(description_edit)
        description_info = create_info_label(
            "Provide a detailed description of this specific file, including the type of data and any unique "
            "attributes.")
        file_input_layout.addWidget(description_info)

        remove_button = QPushButton("X")
        remove_button.clicked.connect(partial(self.remove_file_input, file_input_widget))
        file_input_layout.addWidget(remove_button)

        self.files_layout.addWidget(file_input_widget)

    def remove_file_input(self, widget):
        widget.deleteLater()
        self.update_file_labels()

    def update_file_labels(self):
        for i in range(self.files_layout.count()):
            file_widget = self.files_layout.itemAt(i).widget()
            if file_widget:
                label = file_widget.layout().itemAt(0).widget()  # The QLabel is the first widget in the QHBoxLayout
                label.setText(f"File path for file {i + 1}:")

    def close_app(self):
        self.reject()
        QApplication.instance().exit()  # Exit the application

    def browse_files(self, file_edit):
        file, _ = QFileDialog.getOpenFileName(self, "Select a data file", "",
                                              "CSV Files (*.csv);;ZIP Files (*.zip);;All Files (*)")
        if file:
            file_edit.setText(file)

    def get_project_details(self):
        project_name = self.project_name_edit.text()
        general_description = self.general_description_edit.toPlainText()
        files = []
        descriptions = []
        for i in range(self.files_layout.count()):  # Iterate through all widgets in files_layout
            file_widget = self.files_layout.itemAt(i).widget()
            if file_widget:  # Ensure the widget exists
                layout = file_widget.layout()
                file_edit = layout.itemAt(1).widget()
                description_edit = layout.itemAt(3).widget()

                file_path = file_edit.text()
                description = description_edit.toPlainText()
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
