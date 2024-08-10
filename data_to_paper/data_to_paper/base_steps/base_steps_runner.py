import glob
import json
import os
import shutil
from dataclasses import dataclass, field

from pathlib import Path
from typing import Union, Type, Optional, Dict, Callable

from data_to_paper.base_products.file_descriptions import CreateDataFileDescriptions
from data_to_paper.env import FOLDER_FOR_RUN
from data_to_paper.interactive.base_app_startup import BaseStartDialog
from data_to_paper.servers.api_cost import StageToCost
from data_to_paper.utils.file_utils import clear_directory
from data_to_paper.utils.print_to_file import print_and_log, console_log_file_context
from data_to_paper.servers.llm_call import OPENAI_SERVER_CALLER, OpenaiServerCaller
from data_to_paper.servers.crossref import CROSSREF_SERVER_CALLER
from data_to_paper.servers.semantic_scholar import SEMANTIC_SCHOLAR_SERVER_CALLER
from data_to_paper.conversation.stage import Stage, get_all_keys_following_stage
from data_to_paper.conversation.actions_and_conversations import ActionsAndConversations
from data_to_paper.exceptions import TerminateException, ResetStepException
from data_to_paper.base_products import DataFileDescriptions
from data_to_paper.run_gpt_code.code_runner import RUN_CACHE_FILEPATH
from data_to_paper.utils import dedent_triple_quote_str
from data_to_paper.utils.replacer import Replacer

from data_to_paper.base_steps.base_products_conversers import ProductsHandler
from data_to_paper.interactive.app_interactor import AppInteractor
from data_to_paper.interactive import PanelNames, BaseApp


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
    API_USAGE_COST_FILENAME = 'api_usage_cost.json'

    PROJECT_PARAMETERS_FILENAME = 'data-to-paper.json'
    DEFAULT_PROJECT_PARAMETERS = dict()

    APP_STARTUP_CLS = BaseStartDialog

    name = None
    project_parameters: dict = field(default_factory=DEFAULT_PROJECT_PARAMETERS.copy)
    project_directory: Path = None
    temp_folder_to_run_in: Path = FOLDER_FOR_RUN
    actions_and_conversations: ActionsAndConversations = field(default_factory=ActionsAndConversations)
    should_remove_temp_folder: bool = True

    stages_to_conversations_lens: Dict = field(default_factory=dict)

    app: Optional[BaseApp] = None
    cast = None  # Type[Agent]
    should_mock: Union[bool, str] = True

    stages: Type[Stage] = Stage
    current_stage: Stage = None

    _stages_to_api_usage_cost: StageToCost = field(default_factory=StageToCost)
    stages_to_funcs: Dict[Stage, Callable] = None
    is_stage_completed: Dict[Stage, bool] = None

    server_caller: OpenaiServerCaller = None

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

    def _get_current_stage(self):
        return self.current_stage

    def advance_stage(self, stage: Union[Stage, bool]):
        """
        Advance the stage.
        """
        self.current_stage = stage
        self._app_advance_stage(stage=stage)
        self._add_cost_to_stage(stage=stage)
        if stage.name not in self.stages_to_conversations_lens:
            self.stages_to_conversations_lens[stage.name] = len(self.actions_and_conversations.conversations)

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

    def reset_to_stage(self, stage: Stage):
        """
        Reset the current state to the given stage.
        This will delete the openai responses and the api usage cost files up to the given stage.
        """
        self.server_caller.reset_to_stage(stage)

        # delete all conversations in the actions_and_conversations of the steps after and including the step
        conversation_names = list(self.actions_and_conversations.conversations.keys())
        conversations_to_delete = conversation_names[self.stages_to_conversations_lens[stage.name]:]
        for conversation in conversations_to_delete:
            del self.actions_and_conversations.conversations[conversation]

        # delete api usage cost up to the given stage:
        self._stages_to_api_usage_cost.delete_from_stage(stage)
        self.app_send_api_usage_cost()

        self._reset_is_stage_completed(next_stage=stage)

        self._app_clear_stage_to_reset_to()

    def _pre_run_preparations(self):
        self._update_project_parameters()

    def _get_first_uncompleted_stage(self):
        for stage in self.stages:
            if not self.is_stage_completed[stage]:
                return stage
        return None

    def _reset_is_stage_completed(self, next_stage: Optional[Stage] = None):
        """
        Reset is_stage_completed such that it is completed for all stage before the given stage.
        """
        if next_stage is None:
            self.is_stage_completed = {stage: False for stage in self.stages}
        else:
            self.is_stage_completed = {stage: stage < next_stage for stage in self.stages}

    def _run_all_steps(self):
        """
        Run all the steps towards the high level goal.
        """
        self._reset_is_stage_completed()
        while True:
            stage = self._get_first_uncompleted_stage()
            if stage is None:
                break
            try:
                self._run_stage(stage)
            except ResetStepException as e:
                print_and_log(f'Resetting to stage {e.stage.name}')
                self.reset_to_stage(e.stage)
                self._reset_is_stage_completed(next_stage=e.stage)

    def _run_stage(self, stage: Stage):
        self.is_stage_completed[stage] = True
        self.stages_to_funcs[stage]()

    def _get_files_to_keep(self):
        """
        Get the files to keep after the run.
        """
        return [str(self.output_directory / recording_file)
                for recording_file in [
                    self.CODE_RUNNER_CACHE_FILENAME,
                    self.OPENAI_RESPONSES_FILENAME,
                    self.CROSSREF_RESPONSES_FILENAME,
                    self.SEMANTIC_SCHOLAR_RESPONSES_FILENAME,
                    self.API_USAGE_COST_FILENAME,
                ]]

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
        clear_directory(self.temp_folder_to_run_in, create_if_missing=True)

    def _get_path_in_output_directory(self, file_name: str = None):
        return self.output_directory / file_name if self.should_mock else None

    def run_all_steps(self):
        """
        Run all steps and save all created files to the output folder.
        """
        self.server_caller = OPENAI_SERVER_CALLER
        self.server_caller.set_current_stage_callback(self._get_current_stage)
        self.server_caller.set_api_cost_callback(self._add_cost_to_stage)

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
                self._pre_run_preparations()
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

        self._create_or_clean_output_folder()
        self._create_temp_folder_to_run_in()
        with console_log_file_context(self.output_directory / 'console_log.txt'):
            try:
                run()
            finally:
                if self.should_remove_temp_folder:
                    # remove temp folder and all its content:
                    shutil.rmtree(self.temp_folder_to_run_in, ignore_errors=True)

    @classmethod
    def get_project_parameters_from_project_directory(cls, project_directory: Path,
                                                      add_default_parameters: bool = True
                                                      ) -> dict:
        """
        Get the project parameters from the project directory.
        """
        if add_default_parameters:
            project_parameters = cls.DEFAULT_PROJECT_PARAMETERS.copy()
        else:
            project_parameters = {}
        if cls.PROJECT_PARAMETERS_FILENAME:
            with open(project_directory / cls.PROJECT_PARAMETERS_FILENAME) as file:
                input_project_parameters = json.load(file)
            # check that the keys of input_project_parameters are in project_parameters:
            unknown_keys = set(input_project_parameters.keys()) - set(cls.DEFAULT_PROJECT_PARAMETERS.keys())
            if unknown_keys:
                raise ValueError(f'Unknown keys in project parameters: {unknown_keys}')
            project_parameters.update(input_project_parameters)
        return project_parameters

    @classmethod
    def create_project_directory_from_project_parameters(cls, project_directory: Path, project_parameters: dict,
                                                         **kwargs):
        """
        Create the project directory from the project parameters.
        """
        clear_directory(project_directory, create_if_missing=True)
        if cls.PROJECT_PARAMETERS_FILENAME:
            with open(project_directory / cls.PROJECT_PARAMETERS_FILENAME, 'w') as file:
                json.dump(project_parameters, file, indent=4)

    @classmethod
    def check_files_exist(cls, project_directory: Path, project_parameters: dict):
        """
        Check that we have all the files needed for the run.
        raise FileNotFoundError if a file is missing.
        """
        return

    def _update_project_parameters(self):
        """
        Get the project parameters from the project directory.
        """
        self.project_parameters = self.get_project_parameters_from_project_directory(self.project_directory)

    """
    api usage cost
    """

    def _add_cost_to_stage(self, cost: float = 0, stage: Optional[Stage] = None):
        stage = stage or self.current_stage
        self._stages_to_api_usage_cost[stage] = self._stages_to_api_usage_cost.get(stage, 0) + cost
        self._stages_to_api_usage_cost.save_to_json(self.output_directory / self.API_USAGE_COST_FILENAME)
        self.app_send_api_usage_cost()

    def app_send_api_usage_cost(self):
        self._app_send_api_usage_cost(self._stages_to_api_usage_cost)


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
        general_description='',
        data_file_descriptions=[],
    )

    @classmethod
    def get_project_parameters_from_project_directory(cls, project_directory: Path,
                                                      add_default_parameters: bool = True
                                                      ) -> dict:
        """
        Get the project parameters from the project directory.
        """
        project_parameters = super().get_project_parameters_from_project_directory(
            project_directory, add_default_parameters)
        # add data_file descriptions:
        data_file_descriptions = CreateDataFileDescriptions(
                data_files_str_paths=project_parameters['data_filenames'],
                project_directory=project_directory,
                data_files_is_binary=[None] * len(project_parameters['data_filenames']),
            ).get_raw_str_data_file_descriptions()
        project_parameters['data_file_descriptions'] = [
            data_file_description.description for data_file_description in data_file_descriptions]
        project_parameters['general_description'] = data_file_descriptions.general_description
        return project_parameters

    @classmethod
    def create_project_directory_from_project_parameters(cls, project_directory: Path, project_parameters: dict,
                                                         **kwargs):
        """
        Create the project directory from the project parameters.
        """
        project_parameters = project_parameters.copy()
        data_file_descriptions = project_parameters.pop('data_file_descriptions')
        general_description = project_parameters.pop('general_description')
        super().create_project_directory_from_project_parameters(project_directory, project_parameters)
        CreateDataFileDescriptions(project_directory=project_directory,
                                   data_files_str_paths=project_parameters['data_filenames'],
                                   ).create_file_descriptions(general_description=general_description,
                                                              data_file_descriptions=data_file_descriptions)

    @classmethod
    def check_files_exist(cls, project_directory: Path, project_parameters: dict):
        """
        Check that the files exist.
        """
        super().check_files_exist(project_directory, project_parameters)
        CreateDataFileDescriptions(
            project_directory=project_directory,
            data_files_str_paths=project_parameters['data_filenames'],
        ).check_files_exist()

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

    def _pre_run_preparations(self):
        super()._pre_run_preparations()
        self._read_data_file_descriptions()
