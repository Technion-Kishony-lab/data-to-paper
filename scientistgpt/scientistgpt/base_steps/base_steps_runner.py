import glob
import os
import shutil
from dataclasses import dataclass

from pathlib import Path
from typing import Type

from scientistgpt.env import COALESCE_WEB_CONVERSATIONS
from scientistgpt.servers.chatgpt import OPENAI_SERVER_CALLER
from scientistgpt.servers.crossref import CROSSREF_SERVER_CALLER
from scientistgpt.conversation import save_actions_to_file
from scientistgpt.conversation.actions import apply_action
from scientistgpt.conversation.conversation_actions import CreateConversation
from scientistgpt.conversation.stage import append_advance_stage, Stage
from scientistgpt.run_gpt_code.dynamic_code import module_dir
from scientistgpt.base_cast import Agent

from .base_products_conversers import BaseProductsHandler
from .request_code import BASE_GPT_SCRIPT_FILE_NAME
from .types import DataFileDescriptions


@dataclass
class BaseStepsRunner(BaseProductsHandler):
    """
    A base class for running a series of steps whose Products gradually accumulate towards a high level goal.
    """
    ACTIONS_FILENAME = 'conversation_actions.pkl'
    OPENAI_RESPONSES_FILENAME = 'openai_responses.txt'
    CROSSREF_RESPONSES_FILENAME = 'crossref_responses.txt'

    cast = None  # Type[Agent]
    output_directory: Path = None
    data_file_descriptions: DataFileDescriptions = None
    mock_servers: bool = False

    def create_web_conversations(self):
        if not COALESCE_WEB_CONVERSATIONS:
            return
        if self.cast is None:
            return
        for agent in self.cast:
            if agent.get_conversation_name():
                apply_action(CreateConversation(
                    web_conversation_name=agent.get_conversation_name(),
                    participants={agent, self.cast.get_primary_agent()},
                ))

    def advance_stage(self, stage: Stage):
        """
        Advance the stage of the research goal.
        """
        append_advance_stage(stage=stage)

    @property
    def absolute_data_folder(self):
        return self.data_file_descriptions.data_folder

    def __post_init__(self):
        self.output_directory = Path(self.output_directory).absolute()

    def _run_all_steps(self):
        """
        Run all the steps towards the high level goal.
        """
        raise NotImplementedError

    def create_empty_output_folder(self):
        """
        Create empty output folder (delete all files if exists).
        """
        if os.path.exists(self.output_directory):
            # delete all the files except the mock_openai file:
            for file in glob.glob(str(self.output_directory / '*')):
                if file != str(self.output_directory / self.OPENAI_RESPONSES_FILENAME):
                    os.remove(file)
        else:
            os.makedirs(self.output_directory)

    def run_all_steps(self):
        """
        Run all steps and save all created files to the output folder.
        """
        self.create_empty_output_folder()

        @OPENAI_SERVER_CALLER.record_or_replay(self.output_directory / self.OPENAI_RESPONSES_FILENAME,
                                               should_mock=self.mock_servers)
        @CROSSREF_SERVER_CALLER.record_or_replay(self.output_directory / self.CROSSREF_RESPONSES_FILENAME,
                                                 should_mock=self.mock_servers)
        def run():
            self.create_web_conversations()
            self._run_all_steps()

        try:
            run()
        finally:
            self._save_all_files_to_output_folder()

    def _save_all_files_to_output_folder(self):
        """
        Save all files generated by ScientistGPT to a specified output folder.
        """
        absolute_data_path = self.absolute_data_folder
        output_directory = self.output_directory

        # Save conversation to text file:
        save_actions_to_file(output_directory / self.ACTIONS_FILENAME)

        # Move all gpt analysis result files to output folder:
        for file in glob.glob(str(absolute_data_path / (BASE_GPT_SCRIPT_FILE_NAME + '*.txt'))):
            shutil.move(file, output_directory)

        # Move all gpt analysis scripts to output folder:
        for file in glob.glob(str(Path(module_dir) / (BASE_GPT_SCRIPT_FILE_NAME + '*.py'))):
            shutil.move(file, output_directory)

        # Move all gpt generated plots to output folder:
        for file in glob.glob(str(absolute_data_path / '*.png')):
            shutil.move(file, output_directory)

        # Move gpt generated txt files to output folder:
        for file in glob.glob(str(absolute_data_path / '*.txt')):
            if os.path.basename(file) not in self.data_file_descriptions.get_data_filenames():
                shutil.move(file, output_directory)

        # Move gpt generated pdf files to output folder:
        for file in glob.glob(str(absolute_data_path / '*.pdf')):
            shutil.move(file, output_directory)
