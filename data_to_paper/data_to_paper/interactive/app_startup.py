import json
import sys
from functools import partial

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QApplication, QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog,
                               QMessageBox, QTextEdit, QWidget, QHBoxLayout, QSizePolicy)

from data_to_paper.interactive.get_app import get_or_create_app
from data_to_paper_examples.examples.run_project import get_paper


class PlainTextPasteTextEdit(QTextEdit):
    def insertFromMimeData(self, source):
        if source.hasText():
            # Insert text as plain text, removing any formatting
            self.insertPlainText(source.text())
        else:
            super().insertFromMimeData(source)  # Default behavior for non-text data if needed

class StartDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Set Project Details")
        self.setStyleSheet("background-color: #303030; color: white; font-family: Arial, sans-serif; font-size: 14pt;")
        self.resize(1000, 1000)

        self.layout = QVBoxLayout(self)

        # Top bar layout for close button
        top_bar_layout = QHBoxLayout()
        spacer = QWidget()  # Spacer to push the close button to the right
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        top_bar_layout.addWidget(spacer)

        close_button = QPushButton("Exit")
        close_button.clicked.connect(self.close_app)
        top_bar_layout.addWidget(close_button)

        self.layout.addLayout(top_bar_layout)

        # Input for project name
        self.layout.addWidget(QLabel("Enter the project name:"))
        self.project_name_edit = QLineEdit()
        self.project_name_edit.setStyleSheet("background-color: #151515; color: white;")
        self.layout.addWidget(self.project_name_edit)

        # Input for general description of the dataset
        self.layout.addWidget(QLabel("Enter the general description of the dataset:"))
        self.general_description_edit = PlainTextPasteTextEdit()
        self.general_description_edit.setStyleSheet("background-color: #151515; color: white;")
        self.general_description_edit.setPlaceholderText("The general description of the dataset should include "
                                                         "information about the dataset, its source, and its contents.")
        self.layout.addWidget(self.general_description_edit)

        # Files and descriptions
        self.files_layout = QVBoxLayout()
        self.layout.addLayout(self.files_layout)
        self.add_file_button = QPushButton("Add Another File")
        self.add_file_button.clicked.connect(self.add_file_input)
        self.layout.addWidget(self.add_file_button)

        # Initially add one file input
        self.add_file_input()

        # Large text area for the research goal
        self.layout.addWidget(QLabel("Enter your research goal:"))
        self.goal_edit = PlainTextPasteTextEdit()
        self.goal_edit.setStyleSheet("background-color: #151515; color: white;")
        self.goal_edit.setFixedHeight(100)
        self.goal_edit.setPlaceholderText("optional, if you won't provide it, data-to-paper will devise it for you!")
        self.layout.addWidget(self.goal_edit)

        # Start button
        start_button = QPushButton("Start Project")
        start_button.clicked.connect(self.on_start_clicked)
        self.layout.addWidget(start_button)

        self.load_configuration()


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
        print(project_name + "\n\n" + general_description + "\n\n" + goal + "\n\n" + str(file_paths) + "\n\n" + str(descriptions))
        if project_name and general_description and file_paths and descriptions and len(file_paths) == len(descriptions):
            self.save_configuration()
            self.accept()
        else:
            QMessageBox.warning(None, "Input Required",
                                "Please provide a project name, general description and provide at least one file with its description.")

    def save_configuration(self):
        config = {
            'project_name': self.project_name_edit.text(),
            'general_description': self.general_description_edit.toPlainText(),
            'goal': self.goal_edit.toPlainText(),
            'files': [],
            'descriptions': []
        }
        for i in range(self.files_layout.count()):
            file_widget = self.files_layout.itemAt(i).widget()
            if file_widget:
                layout = file_widget.layout()
                file_edit = layout.itemAt(1).widget()
                description_edit = layout.itemAt(3).widget()
                config['files'].append(file_edit.text())
                config['descriptions'].append(description_edit.toPlainText())

        with open("config/run_setup.json", "w") as json_file:
            json.dump(config, json_file, indent=4)

    def load_configuration(self):
        try:
            with open("config/run_setup.json", "r") as json_file:
                config = json.load(json_file)
            self.project_name_edit.setText(config.get('project_name', ''))
            self.general_description_edit.setPlainText(config.get('general_description', ''))
            self.goal_edit.setPlainText(config.get('goal', ''))
            files = config.get('files', [])
            descriptions = config.get('descriptions', [])

            # Clear existing inputs if any
            while self.files_layout.count():
                widget = self.files_layout.takeAt(0).widget()
                if widget:
                    widget.deleteLater()

            for file_path, description in zip(files, descriptions):
                self.add_file_input()
                file_widget = self.files_layout.itemAt(self.files_layout.count() - 1).widget()
                layout = file_widget.layout()
                file_edit = layout.itemAt(1).widget()
                description_edit = layout.itemAt(3).widget()
                file_edit.setText(file_path)
                description_edit.setPlainText(description)
        except FileNotFoundError:
            pass


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
