import json
import os
import shutil
import glob
from pathlib import Path

from scientistgpt.dynamic_code import module_dir
from scientistgpt.gpt_interactors.scientist_gpt import GPT_SCRIPT_FILENAME, ScientistGPT, ScientistGPT_ANALYSIS_PLAN
from django.conf import settings
from channels.generic.websocket import WebsocketConsumer


class ScientistGPTConsumer(WebsocketConsumer):
    def __init__(self):
        super().__init__()
        self.scientist_gpt = None
        self.experiment_id = None
        self.experiment_folder = None
        self.experiment_data_folder = None
        self.message_filename = 'openai_exchange.txt'

    def handle_message(self, role, message):
        self.send(text_data=json.dumps({"role": role, "message": message}))

    def connect(self):

        self.scientist_gpt = ScientistGPT(run_plan=ScientistGPT_ANALYSIS_PLAN, message_callback=self.handle_message)

        self.accept()

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json['type']

        if message_type == 'start_run_all':
            data_description = text_data_json.get('data_description')
            goal_description = text_data_json.get('goal_description')

            # Update self.scientist_gpt with the new data_description and goal_description
            self.scientist_gpt.data_description = data_description
            self.scientist_gpt.goal_description = goal_description

            self.experiment_id = self.scope['url_route']['kwargs']['experiment_id']

            # Create experiment folder in experiment folder:
            self.experiment_folder = os.path.join(settings.BASE_DIR, self.experiment_id)
            self.experiment_data_folder = os.path.join(self.experiment_folder, 'data')
            if not os.path.exists(self.experiment_folder):
                os.makedirs(self.experiment_folder)
                # copy default data folder to experiment folder
                default_data_folder = os.path.join(settings.BASE_DIR, 'default_data')
                shutil.copytree(default_data_folder, self.experiment_data_folder)

            self.start_run_all()

    def start_run_all(self):

        self.scientist_gpt.run_all(annotate=True)

        # we run in the data folder, so that chatgpt finds out files:
        os.chdir(self.experiment_data_folder)

        """
        Save results
        """
        # Save conversation to text file:
        self.scientist_gpt.conversation.save(self.experiment_folder / self.message_filename)

        # Move all gpt analysis result files to output folder:
        for file in glob.glob(str(self.experiment_data_folder / (GPT_SCRIPT_FILENAME + '*.txt'))):
            shutil.move(file, self.experiment_folder)

        # Move all gpt analysis scripts to output folder:
        for file in glob.glob(str(Path(module_dir) / (GPT_SCRIPT_FILENAME + '*.py'))):
            shutil.move(file, self.experiment_folder)

        # # Move all gpt generated plots to output folder:
        for file in glob.glob(str(self.experiment_data_folder / '*.png')):
            shutil.move(file, self.experiment_folder)

        # Move gpt generated txt files to output folder:
        for file in glob.glob(str(self.experiment_data_folder / '*.txt')):
            shutil.move(file, self.experiment_folder)

    def disconnect(self, close_code):
        pass