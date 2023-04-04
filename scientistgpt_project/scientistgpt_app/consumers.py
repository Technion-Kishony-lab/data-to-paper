import json
import asyncio
import os
import shutil
import glob
import sys
from pathlib import Path

from scientistgpt.dynamic_code import module_dir
from scientistgpt.gpt_interactors.scientist_gpt import GPT_SCRIPT_FILENAME, ScientistGPT, ScientistGPT_ANALYSIS_PLAN


from channels.generic.websocket import AsyncWebsocketConsumer


class ScientistGPTConsumer(AsyncWebsocketConsumer):
    def __init__(self):
        super().__init__()
        self.scientist_gpt = None
        self.experiment_id = None
        self.data_folder = 'data_for_analysis'
        self.message_filename = 'openai_exchange.txt'
        self.absolute_data_path = Path(self.data_folder).absolute()
        self.absolute_home_path = Path().absolute()
        self.absolute_output_path = None

    async def handle_message(self, role, message):
        await self.send(text_data=json.dumps({"role": role, "message": message}))

    async def connect(self):
        self.experiment_id = self.scope['url_route']['kwargs']['experiment_id']


        """
        instantiate ScientistGPT
        """
        OUTPUTS_FOLDER = self.experiment_id
        self.absolute_output_path = Path(OUTPUTS_FOLDER).absolute()
        # Create empty output folder (delete if exists):
        if os.path.exists(self.absolute_output_path):
            shutil.rmtree(self.absolute_output_path)
        os.makedirs(self.absolute_output_path)

        # we run in the data folder, so that chatgpt finds out files:
        os.chdir(self.absolute_data_path)

        self.scientist_gpt = ScientistGPT(run_plan=ScientistGPT_ANALYSIS_PLAN, message_callback=self.handle_message)

        await self.accept()


    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json['type']

        if message_type == 'start_run_all':
            data_description = text_data_json.get('data_description')
            goal_description = text_data_json.get('goal_description')

            # Update self.scientist_gpt with the new data_description and goal_description
            self.scientist_gpt.data_description = data_description
            self.scientist_gpt.goal_description = goal_description
            await self.start_run_all()

    async def start_run_all(self):

        await self.scientist_gpt.run_all(annotate=True)

        os.chdir(self.absolute_home_path)

        """
        Save results
        """
        # Save conversation to text file:
        self.scientist_gpt.conversation.save(self.absolute_output_path / self.message_filename)

        # Move all gpt analysis result files to output folder:
        for file in glob.glob(str(self.absolute_data_path / (GPT_SCRIPT_FILENAME + '*.txt'))):
            shutil.move(file, self.absolute_output_path)

        # Move all gpt analysis scripts to output folder:
        for file in glob.glob(str(Path(module_dir) / (GPT_SCRIPT_FILENAME + '*.py'))):
            shutil.move(file, self.absolute_output_path)

        # Move all gpt generated plots to output folder:
        for file in glob.glob(str(self.absolute_data_path / '*.png')):
            shutil.move(file, self.absolute_output_path)

        # Move gpt generated txt files to output folder:
        for file in glob.glob(str(self.absolute_data_path / '*.txt')):
            shutil.move(file, self.absolute_output_path)

    async def disconnect(self, close_code):
        pass