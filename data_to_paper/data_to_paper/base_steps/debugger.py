import os

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Set, Tuple

from data_to_paper.env import SUPPORTED_PACKAGES, MAX_SENSIBLE_OUTPUT_SIZE, MAX_SENSIBLE_OUTPUT_SIZE_TOKENS, \
    MAX_MODEL_ENGINE
from data_to_paper.utils import dedent_triple_quote_str
from data_to_paper.conversation.message_designation import RangeMessageDesignation, SingleMessageDesignation

from data_to_paper.run_gpt_code.types import CodeAndOutput
from data_to_paper.run_gpt_code.overrides.dataframes import DataFrameSeriesChange
from data_to_paper.run_gpt_code.code_runner import CodeRunner
from data_to_paper.run_gpt_code.code_utils import FailedExtractingCode, IncompleteBlockFailedExtractingCode
from data_to_paper.run_gpt_code.exceptions import FailedRunningCode, FailedLoadingOutput, \
    CodeUsesForbiddenFunctions, CodeWriteForbiddenFile, CodeReadForbiddenFile, CodeImportForbiddenModule

from data_to_paper.base_cast import Agent
from data_to_paper.servers.openai_models import ModelEngine
from data_to_paper.utils.file_utils import UnAllowedFilesCreated, run_in_directory
from data_to_paper.utils.text_extractors import extract_to_nearest_newline

from .base_products_conversers import ProductsConverser
from ..servers.chatgpt import count_number_of_tokens_in_message


@dataclass
class DebuggerConverser(ProductsConverser):
    """
    Interact with chatgpt to debug a code that needs to create an output file.

    Starting with a conversation which ends with a code-request from the user, DebuggerConverser interacts
    with chatgpt to enhance the code until it runs properly and creates a desired output file.

    Interactions with chatgpt include adequate reporting of:
    * missing packages
    * trying to load wrong files
    * syntax errors
    * runtime exceptions
    * too long runs (timeout)
    * output file not created
    """
    model_engine: ModelEngine = field(default_factory=lambda: ModelEngine.GPT35_TURBO)
    allowed_created_files: Tuple[str, ...] = None
    allow_dataframes_to_change_existing_series: bool = True
    enforce_saving_altered_dataframes: bool = False

    user_initiation_prompt: str = None

    assistant_agent: Agent = None
    user_agent: Agent = None

    max_debug_iterations: int = 5

    debug_iteration = 0
    initiation_tag: Optional[str] = None

    previous_code: Optional[str] = None
    gpt_script_filename: str = 'debugger_gpt'
    data_files: Optional[list] = field(default_factory=list)
    data_folder: Path = None
    output_filename: str = 'results.txt'

    @property
    def iteration_str(self):
        return f'Debug iteration {self.debug_iteration}/{self.max_debug_iterations}'

    @property
    def script_filename(self):
        return f'{self.gpt_script_filename}_{self.debug_iteration}'

    def _get_code_runner(self, response: str) -> CodeRunner:
        return CodeRunner(response=response,
                          allowed_read_files=self.data_files,
                          output_file=self.output_filename,
                          allowed_created_files=self.allowed_created_files,
                          allow_dataframes_to_change_existing_series=self.allow_dataframes_to_change_existing_series,
                          script_file_path=None,
                          data_folder=self.data_folder,
                          )
    # to save the script file:
    # script_file_path=self.output_directory / self.script_filename if self.output_directory else None

    def _respond_to_allowed_packages(self, error_message: str):
        self.apply_append_user_message(
            content=dedent_triple_quote_str("""
            I ran the code and got the following error message:
            ```
            {}
            ```
            Please rewrite the code using only these packages: {}. 
            """).format(error_message, SUPPORTED_PACKAGES),
            comment=f'{self.iteration_str}: ImportError detected in gpt code.')

    def _respond_to_file_not_found(self, error_message: str):
        self.apply_append_user_message(
            content=dedent_triple_quote_str("""
            I ran the code and got the following error message:
            ```
            {}
            ```
            As noted in the data description, we only have {}.  

            Files are located in the same directory as the code. 
            """).format(error_message, self.data_files),
            comment=f'{self.iteration_str}: FileNotFound detected in gpt code.')

    def _respond_to_error_message(self, error_message: str, is_warning: bool = False):
        self.apply_append_user_message(
            content=dedent_triple_quote_str("""
            I ran the code and got the following {} message:
            ```
            {}
            ```
            Please rewrite the complete code again with this error corrected. 
            """).format('warning' if is_warning else 'error', error_message),
            comment=f'{self.iteration_str}: Runtime exception in GPT code.')

    def _respond_to_missing_output(self):
        self.apply_append_user_message(
            content=dedent_triple_quote_str("""
            I ran the code. It ran fine without raising any exception, 
            but it didn't generate the desired output file ({}).
            Please rewrite the complete code again so that the output file is correctly created. 
            """).format(self.output_filename),
            comment=f'{self.iteration_str}: Code completed, but no output file created.')

    def _respond_to_unsaved_dataframes(self, read_but_unsaved_dataframe_files: Set[str]):
        self.apply_append_user_message(
            content=dedent_triple_quote_str(f"""
            I see that your code modifies some of the dataframes {read_but_unsaved_dataframe_files}. \
            I would like the code to save any such modified dataframe.  
            Please rewrite the complete code again adding `to_csv` to save any modified dataframe in a new file \
            in the same directory as the code.
            """),
            comment=f'{self.iteration_str}: Code completed, but not all modified dataframes were saved.')

    def _respond_to_timeout(self):
        self.apply_append_user_message(
            content=dedent_triple_quote_str("""
            I ran the code, but it just ran forever...
            Please fix and rewrite the complete code again so that it doesn't get stuck. 
            """),
            comment=f'{self.iteration_str}: GPT code has timed out.')

    def _respond_to_incomplete_code(self):
        if self.model_engine < MAX_MODEL_ENGINE:
            self.model_engine = self.model_engine.get_next()
            response = f"Your sent incomplete code. Let's bump you up to " \
                       f"{self.model_engine.get_next()} and retry!"
        else:
            response = "Your sent incomplete code. Please regenerate response."
        self.apply_append_user_message(
            content=response,
            comment=f'{self.iteration_str}: GPT code is incomplete.')

        # delete the last two messages (incomplete code and this just-posted user response):
        self.apply_delete_messages((-2, -1))

    def _respond_to_missing_or_multiple_code(self, e: FailedExtractingCode):
        """
        We notify missing or incomplete code to chatgpt.
        If the conversation already has this notification, we regenerate gpt response instead.
        """
        self.apply_append_user_message(
            content=str(e),
            tag='failed_extracting_code',
            comment=f'{self.iteration_str}: Failed extracting code from gpt response. Notifying.'
        )

    def _respond_to_forbidden_functions(self, func: str):
        if func == 'print':
            if self.output_filename is None:
                self.apply_append_user_message(
                    content=dedent_triple_quote_str("""
                    Please do not use the `print` function.
                    Your code should only save any new or modified dataframes; should have no other output.
                    """)
                )
            else:
                self.apply_append_user_message(
                    content=dedent_triple_quote_str("""
                    Please do not use the `print` function. 
                    Anything you want to print must be written to the output file ("{}"). 
                    """).format(self.output_filename),
                    comment=f'{self.iteration_str}: Code uses `print`.'
                )
            return
        self.apply_append_user_message(
            content=dedent_triple_quote_str("""
            Your code uses the function `{}`, which is not allowed.
            Please rewrite the complete code again without using this function. 
            """).format(func),
            comment=f'{self.iteration_str}: Code uses forbidden function {func}.')

    def _respond_to_forbidden_import(self, module: str):
        self.apply_append_user_message(
            content=dedent_triple_quote_str("""
            Your code import the module `{}`, which is not allowed.
            Please rewrite the complete code again without using this module. 
            """).format(module),
            comment=f'{self.iteration_str}: Code imports forbidden module {module}.')

    @property
    def only_write_to_description(self):
        if self.output_filename is None:
            if self.allowed_created_files == ('*.csv', ):
                return 'Your code should only save new or modified dataframes to csv files; ' \
                       'it should have no other output.'
            elif self.allowed_created_files:
                return f'Your code should only write to these files: {self.allowed_created_files}.'
            else:
                return 'Your code should not write to any file.'
        else:
            if self.allowed_created_files == ('*.csv', ):
                return f'Your code should save new or modified dataframes to csv files, ' \
                       f'and save other results to the output file "{self.output_filename}".'
            elif self.allowed_created_files:
                return f'Your code should only write to files: {self.allowed_created_files}, ' \
                       f'and to the output file "{self.output_filename}".'
            else:
                return f'Your code should only write to the output file "{self.output_filename}".'

    def _respond_to_forbidden_write(self, file: str):
        self.apply_append_user_message(
            content=dedent_triple_quote_str("""
            Your code writes to the file "{}" which is not allowed.
            {only_write_to_description}
            Please rewrite the complete code again so that it does not create un-allowed files.
            """).format(file, only_write_to_description=self.only_write_to_description),
            comment=f'{self.iteration_str}: Code writes to forbidden file {file}.')

    def _respond_to_un_allowed_files_created(self, files: List[str]):
        self.apply_append_user_message(
            content=dedent_triple_quote_str("""
            Your code creates the following files {} which is not allowed.
            {only_write_to_description}
            Please rewrite the complete code again so that it does not create un-allowed files.
            """).format(files, self.only_write_to_description),
            comment=f'{self.iteration_str}: Code created forbidden files {files}.')

    def _respond_to_forbidden_read(self, file: str):
        if file == self.output_filename:
            self.apply_append_user_message(
                content=dedent_triple_quote_str("""
                I ran the code, but it tried to read from the output file "{}".
                The code should create and write to this output file, but should not read from it.
                Please rewrite the complete code again, making sure it does not read from the output file.
                Note that the input files from which we can read the data are: {}. 
                """).format(file, self.data_files),
                comment=f'{self.iteration_str}: Code reads from output file {file}.')
            return
        else:
            self.apply_append_user_message(
                content=dedent_triple_quote_str("""
                Your code reads from the file "{}" which is not part of the dataset.
                Please rewrite the complete code again, noting that we only have {}. 
                """).format(file, self.data_files),
                comment=f'{self.iteration_str}: Code reads from forbidden file {file}.')

    def _respond_to_dataframe_series_change(self, series: str):
        self.apply_append_user_message(
            content=dedent_triple_quote_str(f"""
            Your code changes the series "{series}" of your dataframe.
            Instead of changing an existing dataframe series, please create a new series, and give it a \
            new sensible name.
            Please rewrite the complete code again, making sure you create new series instead of changing existing ones. 
            """),
            comment=f'{self.iteration_str}: Code modifies dataframe series "{series}".')

    def _respond_to_empty_output(self):
        self.apply_append_user_message(
            content=dedent_triple_quote_str("""
            I ran the code, it created the output file "{}", but the file is just empty! 
            Please rewrite the complete code again to correct this error. 
            """).format(self.output_filename),
            comment=f'{self.iteration_str}: Code completed, but output file is empty.')

    def _respond_to_large_output(self, output: str):
        print(f'ChatGPT code created the following too-long output:\n{output}')
        self.apply_append_user_message(
            content=dedent_triple_quote_str("""
            I ran the code, it created the output file "{}", but the file is too long!

            Here is the beginning of the output:
            ```
            {}
            ```

            Please rewrite the complete code so that only sensible length output is written to the file. 
            """).format(self.output_filename, extract_to_nearest_newline(output, MAX_SENSIBLE_OUTPUT_SIZE.val)),
            comment=f'{self.iteration_str}: Code completed, but output file is too long.')

    def _get_and_run_code(self) -> Optional[CodeAndOutput]:
        """
        Get a code from chatgpt, run it and return code and result.
        If the code fails, notify chatgpt and return None.
        """
        response = self.apply_get_and_append_assistant_message(is_code=True, previous_code=self.previous_code).content
        code_and_output = None
        code_runner = self._get_code_runner(response)
        try:
            code_and_output = code_runner.run_code()
            dataframe_operations = code_and_output.dataframe_operations
        except IncompleteBlockFailedExtractingCode:
            self._respond_to_incomplete_code()
        except FailedExtractingCode as e:
            self._respond_to_missing_or_multiple_code(e)
        except FailedRunningCode as e:
            # We were able to extract the code, but it failed to run
            # We first clean up, re-reposting the code as if it was the immediate response
            self.apply_delete_messages(
                message_designation=RangeMessageDesignation.from_(
                    SingleMessageDesignation(tag=self.initiation_tag, off_set=1), -1),  # keeps the last 2 messages
                comment="Deleting previous debug iterations.")
            self.apply_append_surrogate_message(
                'Here is the code to perform the requested analysis:\n```python\n{}\n```'.format(
                    code_runner.extract_code()),
                web_conversation_name=None,
                comment='We are re-posting the code as if it was the immediate response.')
            self.previous_code = code_runner.extract_code()
            try:
                raise e.exception
            except ImportError:
                # chatgpt tried using a package we do not support
                self._respond_to_allowed_packages(str(e.exception))
            except TimeoutError:
                # code took too long to run
                self._respond_to_timeout()
            except UnAllowedFilesCreated as e:
                # code created files that we do not allow
                self._respond_to_un_allowed_files_created(e.un_allowed_files)
            except FileNotFoundError:
                # the code tried to load file that we do not have
                self._respond_to_file_not_found(str(e.exception))
            except CodeUsesForbiddenFunctions as f:
                self._respond_to_forbidden_functions(f.func)
            except CodeImportForbiddenModule as f:
                self._respond_to_forbidden_import(f.module)
            except CodeWriteForbiddenFile as f:
                self._respond_to_forbidden_write(f.file)
            except CodeReadForbiddenFile as f:
                self._respond_to_forbidden_read(f.file)
            except DataFrameSeriesChange as f:
                self._respond_to_dataframe_series_change(f.changed_series)
            except Warning:
                # the code raised a warning
                self._respond_to_error_message(e.get_traceback_message(), is_warning=True)
            except Exception:
                # the code failed on other errors
                # we will indicate to chatgpt the error message that we got
                self._respond_to_error_message(e.get_traceback_message())
        except FailedLoadingOutput:
            # Code ran, but the output file was not created.
            self._respond_to_missing_output()
        except Exception:
            raise
        else:
            # The code ran without raising exceptions
            output = code_and_output.output
            if output is not None and len(output.strip()) == 0:
                # The code ran successfully, but the output file is empty.
                self._respond_to_empty_output()
            elif output is not None \
                    and count_number_of_tokens_in_message(output, max(ModelEngine)) > \
                    MAX_SENSIBLE_OUTPUT_SIZE_TOKENS.val:
                # The code ran successfully, but the output file is too large.
                self._respond_to_large_output(output)
            elif self.enforce_saving_altered_dataframes \
                    and dataframe_operations.get_read_changed_but_unsaved_ids():
                # The code ran successfully, but not all changed dataframes were saved to files.
                read_but_unsaved_filenames = dataframe_operations.get_read_filenames_from_ids(
                    dataframe_operations.get_read_changed_but_unsaved_ids())
                self._respond_to_unsaved_dataframes(read_but_unsaved_filenames)
            else:
                # All good!
                self.apply_append_user_message('Well done - your code runs successfully!', ignore=True)
                self.comment("GPT code completed successfully.")
                return code_and_output

        # if the code ran, but output was incorrect, we delete any created output files:
        if code_and_output is not None:
            with run_in_directory(self.data_folder):
                for file in code_and_output.created_files:
                    os.remove(file)

        return None  # code failed

    def _get_tag(self):
        """
        If the last message has a tag, use it as the initiation tag.
        Otherwise, create a new tag tagged comment and use it as the initiation tag.
        """
        if self.initiation_tag is None:
            if self.conversation[-1].tag:
                self.initiation_tag = self.conversation[-1].tag
            else:
                raise ValueError("The last message must have a tag.")

    def run_debugging(self) -> Optional[CodeAndOutput]:
        """
        Run the debugging process.
        If debugging did not converge to a running code within the max_debug_iterations, return None.
        Otherwise, return the code and output.
        """
        self.initialize_conversation_if_needed()
        self._get_tag()
        for self.debug_iteration in range(1, self.max_debug_iterations + 1):
            code_and_output = self._get_and_run_code()
            if code_and_output is not None:
                return code_and_output
        self.apply_append_user_message(
            "It seems like we are not converging. Let's try again from the start.\n"
            "Please provide a fresh new attempt of the code.", ignore=True)
        return None
