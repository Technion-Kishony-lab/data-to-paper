import os
from dataclasses import dataclass, field
from typing import Optional

from g3pt.conversation.message_designation import RangeMessageDesignation, SingleMessageDesignation
from g3pt.cast import Agent
from g3pt.base_steps.converser_gpt import ConverserGPT
from g3pt.base_steps.types import CodeAndOutput
from g3pt.run_gpt_code.code_runner import CodeRunner
from g3pt.env import SUPPORTED_PACKAGES, MAX_SENSIBLE_OUTPUT_SIZE
from g3pt.utils import dedent_triple_quote_str
from g3pt.run_gpt_code.exceptions import FailedExtractingCode, FailedRunningCode, FailedLoadingOutput, \
    CodeUsesForbiddenFunctions, CodeWriteForbiddenFile, CodeReadForbiddenFile, CodeImportForbiddenModule


@dataclass
class DebuggerGPT(ConverserGPT):
    """
    Interact with chatgpt to debug a code that needs to create an output file.

    Starting with a conversation which ends with a code-request from the user, DebuggerGPT interacts with chatgpt to
    enhance the code until it runs properly and creates a desired output file.

    Interactions with chatgpt include adequate reporting of:
    * missing packages
    * trying to load wrong files
    * syntax errors
    * runtime exceptions
    * too long runs (timeout)
    * output file not created
    """

    assistant_agent: Agent = None
    user_agent: Agent = None

    max_debug_iterations: int = 5

    debug_iteration = 0
    initiation_tag: Optional[str] = None

    previous_code: Optional[str] = None
    gpt_script_filename: str = 'debugger_gpt'
    data_files: Optional[list] = field(default_factory=list)
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
                          script_file=self.script_filename,
                          )

    def _run_code_runner(self, code_runner: CodeRunner) -> CodeAndOutput:
        result = code_runner.run_code()
        os.rename(self.output_filename, self.script_filename + '.txt')
        return result

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

    def _respond_to_timeout(self):
        self.apply_append_user_message(
            content=dedent_triple_quote_str("""
            I ran the code, but it just ran forever...
            Please fix and rewrite the complete code again so that it doesn't get stuck. 
            """),
            comment=f'{self.iteration_str}: GPT code has timed out.')

    def _respond_to_missing_or_incomplete_code(self, number_of_code_edges: int):
        """
        We notify missing or incomplete code to chatgpt.
        If the conversation already has this notification, we regenerate gpt response instead.
        """
        if number_of_code_edges == 0:
            response = dedent_triple_quote_str("""
            You did not send any code. 
            Please try again, make sure your code is enclosed within triple-backticks.
            """)
            tag = 'no_code'
        elif number_of_code_edges % 2 == 1:
            response = dedent_triple_quote_str("""
            Your code is incomplete. Please try again with a shorter code. Remove comments to help condense the code
            into a single code block.
            """)
            tag = 'incomplete_code'
        else:
            response = dedent_triple_quote_str("""
            Please send your code in a single code block.
            """)
            tag = 'multiple_code_blocks'

        # We use a tagged message to rewind back in case the same problem repeats
        self.apply_append_user_message(
            content=response,
            tag=tag,
            comment=f'{self.iteration_str}: Failed extracting code from gpt response. Notifying.'
        )

    def _respond_to_forbidden_functions(self, func: str):
        if func == 'print':
            self.apply_append_user_message(
                content=dedent_triple_quote_str("""
                Please do not use the `print` function. 
                Anything you want to print, must be written to the output file. 
                """),
                comment=f'{self.iteration_str}: Code uses `print`.')
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

    def _respond_to_forbidden_write(self, file: str):
        self.apply_append_user_message(
            content=dedent_triple_quote_str("""
            I ran the code, but it tried to write to the file `{}` which is not allowed.
            Please rewrite the complete code again, making sure it only writes to "{}". 
            """).format(file, self.output_filename),
            comment=f'{self.iteration_str}: Code writes to forbidden file {file}.')

    def _respond_to_forbidden_read(self, file: str):
        self.apply_append_user_message(
            content=dedent_triple_quote_str("""
            I ran the code, but it tried to read from the file `{}` which is not part of the dataset.
            Please rewrite the complete code again, noting that we only have {}. 
            """).format(file, self.data_files),
            comment=f'{self.iteration_str}: Code reads from forbidden file {file}.')

    def _respond_to_empty_output(self):
        self.apply_append_user_message(
            content=dedent_triple_quote_str("""
            I ran the code, it created the output file {}, but the file is just empty! 
            Please rewrite the complete code again to correct this error. 
            """).format(self.output_filename),
            comment=f'{self.iteration_str}: Code completed, but output file is empty.')

    def _respond_to_large_output(self):
        self.apply_append_user_message(
            content=dedent_triple_quote_str("""
            I ran the code, it created the output file {}, but the file is too long!
            Please rewrite the complete code so that only sensible length output is written to the file. 
            """).format(self.output_filename),
            comment=f'{self.iteration_str}: Code completed, but output file is too long.')

    def _get_and_run_code(self) -> Optional[CodeAndOutput]:
        """
        Get a code from chatgpt, run it and return code and result.
        If the code fails, notify chatgpt and return None.
        """
        response = self.apply_get_and_append_assistant_message(is_code=True, previous_code=self.previous_code)
        failed_extracting_code = False
        code_runner = self._get_code_runner(response)
        try:
            code_and_output = self._run_code_runner(code_runner)
        except FailedExtractingCode as e:
            # code is missing or incomplete
            failed_extracting_code = True
            self._respond_to_missing_or_incomplete_code(e.number_of_code_edges)
        except FailedRunningCode as e:
            # We were able to extract the code, but it failed to run
            self.previous_code = code_runner.extract_code()
            try:
                raise e.exception
            except ImportError:
                # chatgpt tried using a package we do not support
                self._respond_to_allowed_packages(str(e.exception))
            except TimeoutError:
                # code took too long to run
                self._respond_to_timeout()
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
            if len(output.strip()) == 0:
                # The code ran successfully, but the output file is empty.
                self._respond_to_empty_output()
            elif len(output) > MAX_SENSIBLE_OUTPUT_SIZE:
                # The code ran successfully, but the output file is too large.
                self._respond_to_large_output()
            else:
                # All good!
                self.comment("GPT code completed successfully. Returning results to ScientistGPT.")
                return code_and_output

        # if code was extracted ok, we clean up a bit, deleting the previous debug iterations
        if not failed_extracting_code:
            self.conversation_manager.delete_messages(
                message_designation=RangeMessageDesignation.from_(
                    SingleMessageDesignation(tag=self.initiation_tag, off_set=1), -3),  # keeps the last 2 messages
                comment="Deleting previous debug iterations.")
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
        return None
