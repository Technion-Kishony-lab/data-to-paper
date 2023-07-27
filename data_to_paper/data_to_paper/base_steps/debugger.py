import importlib
import os

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Set, Tuple

from data_to_paper.env import SUPPORTED_PACKAGES, MAX_MODEL_ENGINE
from data_to_paper.utils import dedent_triple_quote_str, line_count

from data_to_paper.run_gpt_code.types import CodeAndOutput, OutputFileRequirement, \
    get_single_content_file_from_requirements, ContentOutputFileRequirement
from data_to_paper.run_gpt_code.overrides.dataframes import DataFrameSeriesChange
from data_to_paper.run_gpt_code.code_runner import CodeRunner
from data_to_paper.run_gpt_code.code_utils import FailedExtractingBlock, IncompleteBlockFailedExtractingBlock
from data_to_paper.run_gpt_code.overrides.dataframes.df_methods.raise_on_call import UnAllowedDataframeMethodCall
from data_to_paper.run_gpt_code.exceptions import FailedRunningCode, \
    CodeUsesForbiddenFunctions, CodeWriteForbiddenFile, CodeReadForbiddenFile, CodeImportForbiddenModule

from data_to_paper.servers.chatgpt import count_number_of_tokens_in_message
from data_to_paper.base_cast import Agent
from data_to_paper.servers.openai_models import ModelEngine
from data_to_paper.utils.file_utils import UnAllowedFilesCreated, run_in_directory
from data_to_paper.utils.text_extractors import extract_to_nearest_newline

from .base_products_conversers import BackgroundProductsConverser


KNOWN_MIS_IMPORTS = {
    'Mediation': 'statsmodels.stats.mediation',
}

# assert KNOWN_MIS_IMPORTS:
for name, module in KNOWN_MIS_IMPORTS.items():
    try:
        importlib.import_module(module, name)
    except ImportError:
        raise ImportError(f"Wong imports in KNOWN_MIS_IMPORTS.\nFailed importing {name} from {module}")


@dataclass
class DebuggerConverser(BackgroundProductsConverser):
    """
    Interact with ChatGPT to debug a code that needs to create an output file.

    Starting with a conversation which ends with a code-request from the user, DebuggerConverser interacts
    with ChatGPT to enhance the code until it runs properly and creates a desired output file.

    Interactions with chatgpt include adequate reporting of:
    * missing packages
    * trying to load wrong files
    * syntax errors
    * runtime exceptions
    * too long runs (timeout)
    * output file not created
    """

    # input files:
    data_folder: Path = None
    data_filenames: Optional[list] = field(default_factory=list)

    # output files:
    output_file_requirements: Tuple[OutputFileRequirement, ...] = ()

    # dataframes:
    allow_dataframes_to_change_existing_series: bool = True
    enforce_saving_altered_dataframes: bool = False

    user_initiation_prompt: str = None
    assistant_agent: Agent = None
    user_agent: Agent = None

    supported_packages: Tuple[str, ...] = SUPPORTED_PACKAGES
    runner_cls: CodeRunner = CodeRunner

    max_debug_iterations: int = 5
    debug_iteration = 0

    previous_code: Optional[str] = None
    _requesting_modifications: bool = False
    gpt_script_filename: str = 'debugger_gpt'

    @property
    def output_filenames(self) -> Tuple[str, ...]:
        return tuple(output_file_requirement.filename for output_file_requirement in self.output_file_requirements)

    @property
    def output_filename(self) -> Optional[str]:
        return get_single_content_file_from_requirements(self.output_file_requirements)

    @property
    def iteration_str(self):
        return f'Debug iteration {self.debug_iteration}/{self.max_debug_iterations}'

    @property
    def script_filename(self):
        return f'{self.gpt_script_filename}_{self.debug_iteration}'

    def _get_code_runner(self, response: str) -> CodeRunner:
        return self.runner_cls(response=response,
                               allowed_read_files=self.data_filenames,
                               output_file_requirements=self.output_file_requirements,
                               allow_dataframes_to_change_existing_series=self.allow_dataframes_to_change_existing_series,
                               script_file_path=None,
                               data_folder=self.data_folder,
                               )
    # to save the script file:
    # script_file_path=self.output_directory / self.script_filename if self.output_directory else None

    def _respond_to_known_mis_imports(self, e: ImportError) -> bool:
        if not hasattr(e, 'fromlist'):
            return False
        if len(e.fromlist) != 1:
            return False
        var = e.fromlist[0]
        if var not in KNOWN_MIS_IMPORTS:
            return False
        correct_package = KNOWN_MIS_IMPORTS[var]
        # extract from correct_package up to the first '.':
        package_base = correct_package[:correct_package.index('.')] if '.' in correct_package else correct_package
        if package_base not in self.supported_packages:
            return False
        self.apply_append_user_message(
            content=dedent_triple_quote_str("""
            I ran the code and got the following error message:
            ```
            {}
            ```
            Please rewrite the code using only these packages: {supported_packages}.
            Note that there is a `{var}` in `{correct_package}`. Is this perhaps what you needed? 
            """).format(e, supported_packages=self.supported_packages, var=var, correct_package=KNOWN_MIS_IMPORTS[var]),
            comment=f'{self.iteration_str}: ImportError detected in gpt code.')
        return True

    def _respond_to_allowed_packages(self, e: ImportError):
        if self._respond_to_known_mis_imports(e):
            return
        self.apply_append_user_message(
            content=dedent_triple_quote_str("""
            I ran the code and got the following error message:
            ```
            {}
            ```
            Please rewrite the code using only these packages: {}. 
            """).format(e, self.supported_packages),
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
            """).format(error_message, self.data_filenames),
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

    def _respond_to_missing_output(self, requirement: OutputFileRequirement, filenames: List[str]):
        if requirement.is_wildcard():
            self.apply_append_user_message(
                content=dedent_triple_quote_str(f"""
                I ran the code. It ran fine without raising any exception.
                However, the code was supposed to create at least {requirement.minimal_count} files \
                of "{requirement.filename}", \ 
                but it created {len(filenames)} files of this type.
                Please rewrite the complete code again so that these output files are correctly created. 
                """),
                comment=f'{self.iteration_str}: Code completed, but not enough output files created.')
        else:
            self.apply_append_user_message(
                content=dedent_triple_quote_str(f"""
                I ran the code. It ran fine without raising any exception, 
                but it didn't generate the desired output file ({requirement.filename}).
                Please rewrite the complete code again so that the output file is correctly created. 
                """),
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
        self.apply_delete_messages([-2, -1])

    def _respond_to_missing_or_multiple_code(self, e: FailedExtractingBlock):
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
            if not self.output_filename:
                self.apply_append_user_message(
                    content=dedent_triple_quote_str("""
                    Please do not use the `print` function.
                    Your code should only save any new or modified dataframes; should have no other output.
                    """)
                )
            else:
                self.apply_append_user_message(
                    content=dedent_triple_quote_str(f"""
                    Please do not use the `print` function. 
                    Anything you want to print must be written to the output file ("{self.output_filename}"). 
                    """),
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
            content=dedent_triple_quote_str(f"""
            Your code import the module `{module}`, which is not allowed.
            Please rewrite the complete code again without using this module. 
            """),
            comment=f'{self.iteration_str}: Code imports forbidden module {module}.')

    def _check_code_and_respond(self, code: str):
        return True

    @property
    def description_of_allowed_output_files(self):
        requirements = self.output_file_requirements
        if len(requirements) == 0:
            return 'Your code should not write to any file.'

        return 'Your code should only write to these files: {}.'.format(
            ', '.join(f'"{r.filename}"' for r in requirements)
        )

    def _respond_to_forbidden_write(self, file: str):
        self.apply_append_user_message(
            content=dedent_triple_quote_str("""
            Your code writes to the file "{}" which is not allowed.
            {description_of_allowed_output_files}
            Please rewrite the complete code again so that it does not create un-allowed files.
            """).format(file, description_of_allowed_output_files=self.description_of_allowed_output_files),
            comment=f'{self.iteration_str}: Code writes to forbidden file {file}.')

    def _respond_to_un_allowed_files_created(self, files: List[str]):
        self.apply_append_user_message(
            content=dedent_triple_quote_str("""
            Your code creates the following files {} which is not allowed.
            {description_of_allowed_output_files}
            Please rewrite the complete code again so that it does not create un-allowed files.
            """).format(files, self.description_of_allowed_output_files),
            comment=f'{self.iteration_str}: Code created forbidden files {files}.')

    def _respond_to_forbidden_read(self, file: str):
        if file == self.output_filename:
            self.apply_append_user_message(
                content=dedent_triple_quote_str(f"""
                I ran the code, but it tried to read from the output file "{file}".
                The code should create and write to this output file, but should not read from it.
                Please rewrite the complete code again, making sure it does not read from the output file.
                Note that the input files from which we can read the data are: {self.data_filenames}. 
                """),
                comment=f'{self.iteration_str}: Code reads from output file {file}.')
            return
        else:
            self.apply_append_user_message(
                content=dedent_triple_quote_str("""
                Your code reads from the file "{}" which is not part of the dataset.
                We only have these files:
                {}

                Note that these input files are located in the same directory as the code. 
                Please rewrite the complete code again so that it only reads from these files. 
                """).format(file, self.data_filenames),
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

    def _check_and_response_to_file_content(self, requirement: ContentOutputFileRequirement,
                                            filename: str, content: str) -> Optional[str]:
        if len(content.strip()) == 0:
            # The code ran successfully, but the output file is empty.
            return dedent_triple_quote_str(f"""
                I ran the code, it created the output file "{filename}", but the file is just empty! 
                Please rewrite the complete code again to correct this error. 
                """)
        if count_number_of_tokens_in_message(content, max(ModelEngine)) > requirement.max_tokens:
            # The code ran successfully, but the output file is too large.
            print(f'ChatGPT code created "{filename}" with the following too-long output:\n{content}')
            return dedent_triple_quote_str("""
                I ran the code, it created the output file "{}", but the file is too long!

                Here is the beginning of the output:
                ```output
                {}
                ```

                Please rewrite the complete code so that only sensible length output is written to the file. 
                """).format(filename, extract_to_nearest_newline(content, requirement.max_tokens))

    def _is_output_ok(self, code_and_output: CodeAndOutput) -> bool:
        dataframe_operations = code_and_output.dataframe_operations
        files_to_contents = code_and_output.get_created_content_files_to_contents(is_clean=True)
        for requirement in self.output_file_requirements:
            output_files = list(code_and_output.requirements_to_output_files_to_contents[requirement].keys())
            if len(output_files) < requirement.minimal_count:
                # Code ran, but the specified number of output files were not created.
                self._respond_to_missing_output(requirement, output_files)
                return False

            if isinstance(requirement, ContentOutputFileRequirement):
                for filename in output_files:
                    message = self._check_and_response_to_file_content(
                        requirement, filename, files_to_contents[filename])
                    if message:
                        self.apply_append_user_message(content=message,
                                                       comment=f'file content failed ({filename}) {self.iteration_str}')
                        return False

        if self.enforce_saving_altered_dataframes and dataframe_operations.get_read_changed_but_unsaved_ids():
            # The code ran successfully, but not all changed dataframes were saved to files.
            read_but_unsaved_filenames = dataframe_operations.get_read_filenames_from_ids(
                dataframe_operations.get_read_changed_but_unsaved_ids())
            self._respond_to_unsaved_dataframes(read_but_unsaved_filenames)
            return False

        return True

    def _is_new_code_a_modification_of_old_code(self, new_code: str, old_code: str) -> bool:
        """
        Return True if new_code is a modification of old_code.
        """
        return line_count(new_code) > line_count(old_code) * 0.9

    def _respond_to_incomplete_modification(self):
        self.apply_append_user_message(
            content="Your code does not seem to be a modification of the previous code.",
            comment=f'{self.iteration_str}: Code is not a modification of previous code.')
        # delete the last two messages (wrong code and this just-posted user response):
        self.apply_delete_messages([-2, -1])

    def _get_and_run_code(self) -> Optional[CodeAndOutput]:
        """
        Get a code from chatgpt, run it and return code and result.
        If the code fails, notify chatgpt and return None.
        """
        response = self.apply_get_and_append_assistant_message(is_code=True, previous_code=self.previous_code).content
        code_runner = self._get_code_runner(response)

        try:
            code = code_runner.extract_code()
        except IncompleteBlockFailedExtractingBlock:
            self._respond_to_incomplete_code()
            return None
        except FailedExtractingBlock as e:
            self._respond_to_missing_or_multiple_code(e)
            return None

        # We were able to extract the code. We now check the code before running it.
        if self._requesting_modifications:
            if not self._is_new_code_a_modification_of_old_code(code, self.previous_code):
                # The code is not a modification of the previous code, but we are requesting modifications.
                self._respond_to_incomplete_modification()
                return None
            self._requesting_modifications = False

        if not self._check_code_and_respond(code):
            # The code is not ok, we cannot run it.
            return None

        # We can now run the code.
        # We first clean up, re-reposting the code as if it was the first response
        self._rewind_conversation_to_first_response()
        self.apply_append_surrogate_message(
            'Here is the code to perform the requested analysis:\n```python\n{}\n```'.format(
                code_runner.extract_code()),
            web_conversation_name=None,
            comment='We are re-posting the code as if it was the immediate response.')
        self.previous_code = code
        code_and_output = None
        try:
            code_and_output = code_runner.run_code()
        except FailedRunningCode as e:
            try:
                raise e.exception
            except ImportError as f:
                # chatgpt tried using a package we do not support
                self._respond_to_allowed_packages(f)
            except TimeoutError:
                # code took too long to run
                self._respond_to_timeout()
            except UnAllowedFilesCreated as f:
                # code created files that we do not allow
                self._respond_to_un_allowed_files_created(f.un_allowed_files)
            except FileNotFoundError as f:
                # the code tried to load file that we do not have
                self._respond_to_file_not_found(str(f))
            except CodeUsesForbiddenFunctions as f:
                self._respond_to_forbidden_functions(f.func)
            except UnAllowedDataframeMethodCall as f:
                self._respond_to_forbidden_functions(f.method_name)
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
                self._respond_to_error_message(e.get_traceback_message(code_runner.lines_added_in_front_of_code),
                                               is_warning=True)
            except Exception:
                # the code failed on other errors
                # we will indicate to chatgpt the error message that we got
                self._respond_to_error_message(e.get_traceback_message(code_runner.lines_added_in_front_of_code))
        except Exception:
            raise
        else:
            # The code ran without raising exceptions.
            # We now check if the output is ok:
            if self._is_output_ok(code_and_output):
                # All good!
                self.apply_append_user_message('Well done - your code runs successfully!', ignore=True)
                self.comment("GPT code completed successfully.")
                return code_and_output

        # if the code ran, but output was incorrect, we delete any created files:
        if code_and_output is not None:
            with run_in_directory(self.data_folder):
                for file in code_and_output.get_created_data_files():
                    os.remove(file)

        return None  # code failed

    def run_debugging(self) -> Optional[CodeAndOutput]:
        """
        Run the debugging process.
        If debugging did not converge to a running code within the max_debug_iterations, return None.
        Otherwise, return the code and output.
        """
        self.initialize_conversation_if_needed()
        for self.debug_iteration in range(1, self.max_debug_iterations + 1):
            code_and_output = self._get_and_run_code()
            if code_and_output is not None:
                return code_and_output
        self.apply_append_user_message(
            "It seems like we are not converging. Let's try again from the start.\n"
            "Please provide a fresh new attempt of the code.", ignore=True)
        self._rewind_conversation_to_first_response()

        return None
