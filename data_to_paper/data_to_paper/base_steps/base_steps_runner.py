import glob
import json
import os
import shutil
from dataclasses import dataclass, field

from pathlib import Path
from typing import Union, Type

from data_to_paper.base_products.file_descriptions import CreateDataFileDescriptions
from data_to_paper.env import FOLDER_FOR_RUN
from data_to_paper.utils.file_utils import run_in_directory
from data_to_paper.utils.print_to_file import print_and_log, console_log_file_context
from data_to_paper.servers.llm_call import OPENAI_SERVER_CALLER
from data_to_paper.servers.crossref import CROSSREF_SERVER_CALLER
from data_to_paper.servers.semantic_scholar import SEMANTIC_SCHOLAR_SERVER_CALLER
from data_to_paper.conversation.stage import Stage
from data_to_paper.conversation.actions_and_conversations import ActionsAndConversations
from data_to_paper.exceptions import TerminateException
from data_to_paper.base_products import DataFileDescriptions, DataFileDescription
from data_to_paper.run_gpt_code.code_runner import RUN_CACHE_FILEPATH
from data_to_paper.utils import dedent_triple_quote_str
from data_to_paper.utils.replacer import Replacer

from data_to_paper.base_steps.base_products_conversers import ProductsHandler
from data_to_paper.interactive.app_interactor import AppInteractor
from data_to_paper.interactive import PanelNames


@dataclass
class BaseStepsRunner(ProductsHandler, AppInteractor):
    """
    A base class for running a series of steps whose Products gradually accumulate towards a high level goal.
    """
    ACTIONS_FILENAME = 'conversation_actions.pkl'
    OPENAI_RESPONSES_FILENAME = 'openai_responses.txt'
    CROSSREF_RESPONSES_FILENAME = 'crossref_responses.bin'
    SEMANTIC_SCHOLAR_RESPONSES_FILENAME = 'semantic_scholar_responses.bin'
    CODE_RUNNER_CACHE_FILENAME = 'code_runner_cache.pkl'

    PROJECT_PARAMETERS_FILENAME = 'data-to-paper.json'
    DEFAULT_PROJECT_PARAMETERS = dict()
    project_parameters: dict = field(default_factory=DEFAULT_PROJECT_PARAMETERS.copy)
    project_directory: Path = None
    temp_folder_to_run_in: Path = FOLDER_FOR_RUN
    actions_and_conversations: ActionsAndConversations = field(default_factory=ActionsAndConversations)

    cast = None  # Type[Agent]
    should_mock: Union[bool, str] = True

    stages: Type[Stage] = Stage
    current_stage: Stage = None

    failure_message = dedent_triple_quote_str("""
        ## Run Terminated
        Run terminated prematurely during stage `{current_stage}`.
        ```error
        {exception}
        ```
        """)
    unexpected_error_message = dedent_triple_quote_str("""
        # Run failed.
        *data-to-paper* exited unexpectedly.
        ### Exception:
        ```error
        {exception}
        ```
        """)
    success_message = dedent_triple_quote_str("""
        ## Completed
        This *data-to-paper* research cycle is now completed.
        The manuscript is ready. 

        The created manuscript and all other output files are saved in:
        {output_directory}

        You can click "Compile Paper" stage button to open the manuscript.

        Please check the created manuscript rigorously and carefully.


        *Remember that the process is not error-free and the responsibility for the final manuscript \t
        remains with you.*


        You can close the app now.
        """)

    def __post_init__(self):
        super().__post_init__()
        self._read_project_parameters()

    def advance_stage(self, stage: Stage):
        """
        Advance the stage.
        """
        self.current_stage = stage
        self._app_advance_stage(stage)

    def send_product_to_client(self, product_field: str, save_to_file: bool = False):
        """
        Get the base GPT script file.
        """
        if save_to_file:
            filename = product_field + '.txt'
            with open(self.output_directory / filename, 'w') as file:
                file.write(self.products.get_description(product_field))
        if self.app:
            product = self.products.get_description_as_html(product_field)
            self._app_send_product_of_stage(
                stage=self.products.get_stage(product_field),
                product_text=product,
            )

    def _run_all_steps(self):
        """
        Run all the steps towards the high level goal.
        """
        raise NotImplementedError

    def _get_files_to_keep(self):
        """
        Get the files to keep after the run.
        """
        return [str(self.output_directory / recording_file)
                for recording_file in [
                    self.CODE_RUNNER_CACHE_FILENAME,
                    self.OPENAI_RESPONSES_FILENAME,
                    self.CROSSREF_RESPONSES_FILENAME,
                    self.SEMANTIC_SCHOLAR_RESPONSES_FILENAME]]

    def _create_or_clean_output_folder(self):
        """
        Create empty output folder (delete all files if exists).
        """
        if os.path.exists(self.output_directory):
            # delete all the files except the mock_openai file:
            for file in glob.glob(str(self.output_directory / '*')):
                if file not in self._get_files_to_keep():
                    # the file can be a non-empty directory or a file. remove it anyway:
                    if os.path.isfile(file):
                        os.remove(file)
                    else:
                        shutil.rmtree(file)
        else:
            os.makedirs(self.output_directory)

    def _create_temp_folder_to_run_in(self):
        """
        Create a temporary folder to run the code in.
        """
        if self.temp_folder_to_run_in.exists():
            shutil.rmtree(self.temp_folder_to_run_in)
        self.temp_folder_to_run_in.mkdir()

    def _get_path_in_output_directory(self, file_name: str = None):
        return self.output_directory / file_name if self.should_mock else None

    def run_all_steps(self):
        """
        Run all steps and save all created files to the output folder.
        """

        @RUN_CACHE_FILEPATH.temporary_set(
            self._get_path_in_output_directory(self.CODE_RUNNER_CACHE_FILENAME))
        @SEMANTIC_SCHOLAR_SERVER_CALLER.record_or_replay(
            self._get_path_in_output_directory(self.SEMANTIC_SCHOLAR_RESPONSES_FILENAME))
        @OPENAI_SERVER_CALLER.record_or_replay(
            self._get_path_in_output_directory(self.OPENAI_RESPONSES_FILENAME))
        @CROSSREF_SERVER_CALLER.record_or_replay(
            self._get_path_in_output_directory(self.CROSSREF_RESPONSES_FILENAME))
        def run():
            try:
                self._run_all_steps()
            except TerminateException as e:
                # self.advance_stage(Stage.FAILURE)  # used for the old whatsapp app
                msg = Replacer(self, self.failure_message, kwargs={'exception': str(e)}).format_text()
                self._app_send_prompt(PanelNames.MISSION_PROMPT, msg, from_md=True)
                self._app_set_header('Terminate upon failure')
                print_and_log(f'----- TERMINATING RUN ------\n{msg}\n----------------------------\n')
            except Exception as e:
                self._app_clear_panels()
                msg = Replacer(self, self.unexpected_error_message, kwargs={'exception': str(e)}).format_text()
                self._app_send_prompt(PanelNames.MISSION_PROMPT, msg, from_md=True)
                raise
            else:
                msg = Replacer(self, self.success_message).format_text()
                self._app_send_prompt(PanelNames.MISSION_PROMPT, msg, from_md=True)
                self._app_set_header('Completed')
                print_and_log(f'----- COMPLETED RUN ------\n{msg}\n----------------------------\n')

        with console_log_file_context(self.output_directory / 'console_log.txt'):
            self._create_or_clean_output_folder()
            self._create_temp_folder_to_run_in()
            run()

    def _read_project_parameters(self):
        """
        Get the project parameters from the project directory.
        """
        self.project_parameters = self.DEFAULT_PROJECT_PARAMETERS.copy()
        if self.PROJECT_PARAMETERS_FILENAME:
            with open(self.project_directory / self.PROJECT_PARAMETERS_FILENAME) as file:
                input_project_parameters = json.load(file)
            # check that the keys of input_project_parameters are in self.project_parameters:
            unknown_keys = set(input_project_parameters.keys()) - set(self.project_parameters.keys())
            if unknown_keys:
                raise ValueError(f'Unknown keys in project parameters: {unknown_keys}')
            self.project_parameters.update(input_project_parameters)


@dataclass
class DataStepRunner(BaseStepsRunner):
    """
    A class for running a series of steps towards a high level goal.
    With the ability to handle data files.
    """
    data_file_descriptions: DataFileDescriptions = field(default_factory=DataFileDescriptions)
    DEFAULT_PROJECT_PARAMETERS = dict(
        data_filenames=[],
        data_files_is_binary=[],
        description='',
    )

    def _read_data_file_descriptions(self):
        """
        Read the data file descriptions from the project directory
        """
        self.data_file_descriptions = CreateDataFileDescriptions(
            data_files_str_paths=self.project_parameters['data_filenames'],
            project_directory=self.project_directory,
            data_files_is_binary=self.project_parameters['data_files_is_binary'],
            temp_folder_to_run_in=self.temp_folder_to_run_in,
        ).create_temp_folder_and_get_file_descriptions()
