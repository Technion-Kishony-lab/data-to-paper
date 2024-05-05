import glob
import os
import shutil
from dataclasses import dataclass, field

from pathlib import Path
from typing import Union

from data_to_paper.utils.print_to_file import print_and_log
from data_to_paper.servers.llm_call import OPENAI_SERVER_CALLER
from data_to_paper.servers.crossref import CROSSREF_SERVER_CALLER
from data_to_paper.servers.semantic_scholar import SEMANTIC_SCHOLAR_SERVER_CALLER
from data_to_paper.conversation.stage import Stage
from data_to_paper.conversation.actions_and_conversations import ActionsAndConversations
from data_to_paper.exceptions import TerminateException
from data_to_paper.base_products import DataFileDescriptions
from data_to_paper.run_gpt_code.code_runner import RUN_CACHE_FILEPATH
from data_to_paper.utils import dedent_triple_quote_str
from data_to_paper.utils.replacer import Replacer
from data_to_paper.utils.text_formatting import wrap_text_with_triple_quotes

from .base_products_conversers import ProductsHandler
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

    actions_and_conversations: ActionsAndConversations = field(default_factory=ActionsAndConversations)

    cast = None  # Type[Agent]
    data_file_descriptions: DataFileDescriptions = None
    mock_servers: Union[bool, str] = False

    current_stage: Stage = None

    failure_message = dedent_triple_quote_str("""
        ## Run Terminated
        Run terminated prematurely during stage `{current_stage}`.
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

    @property
    def absolute_data_folder(self):
        return self.data_file_descriptions.data_folder

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

    def create_empty_output_folder(self):
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

    def get_mock_responses_file(self, file_name: str = None):
        if self.mock_servers is False:
            return None
        directory = self.output_directory if self.mock_servers is True else self.mock_servers
        return Path(directory).absolute() / file_name

    @property
    def should_mock(self):
        return self.mock_servers is not False

    def run_all_steps(self):
        """
        Run all steps and save all created files to the output folder.
        """
        self.create_empty_output_folder()

        @RUN_CACHE_FILEPATH.temporary_set(self.output_directory / self.CODE_RUNNER_CACHE_FILENAME)
        @SEMANTIC_SCHOLAR_SERVER_CALLER.record_or_replay(
            self.get_mock_responses_file(self.SEMANTIC_SCHOLAR_RESPONSES_FILENAME), should_mock=self.should_mock)
        @OPENAI_SERVER_CALLER.record_or_replay(
            self.get_mock_responses_file(self.OPENAI_RESPONSES_FILENAME), should_mock=self.should_mock)
        @CROSSREF_SERVER_CALLER.record_or_replay(
            self.get_mock_responses_file(self.CROSSREF_RESPONSES_FILENAME), should_mock=self.should_mock)
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
                self._app_send_prompt(PanelNames.MISSION_PROMPT,
                                      '# Run failed.\n*data-to-paper* exited unexpectedly.\n'
                                      '### Exception:\n'
                                      f'{wrap_text_with_triple_quotes(str(e), "error")}',
                                      from_md=True)
                raise
            else:
                msg = Replacer(self, self.success_message).format_text()
                self._app_send_prompt(PanelNames.MISSION_PROMPT, msg, from_md=True)
                self._app_set_header('Completed')
                print_and_log(f'----- COMPLETED RUN ------\n{msg}\n----------------------------\n')

        run()
