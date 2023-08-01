import importlib
import os

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Set, Tuple, Union

from data_to_paper.env import SUPPORTED_PACKAGES, MAX_MODEL_ENGINE
from data_to_paper.utils import dedent_triple_quote_str, line_count

from data_to_paper.run_gpt_code.types import CodeAndOutput, OutputFileRequirement, \
    get_single_content_file_from_requirements, ContentOutputFileRequirement, CodeProblem, RunIssue
from data_to_paper.run_gpt_code.overrides.dataframes import DataFrameSeriesChange
from data_to_paper.run_gpt_code.code_runner import CodeRunner
from data_to_paper.run_gpt_code.code_utils import FailedExtractingBlock, IncompleteBlockFailedExtractingBlock
from data_to_paper.run_gpt_code.overrides.dataframes.df_methods.raise_on_call import UnAllowedDataframeMethodCall
from data_to_paper.run_gpt_code.run_utils import RunUtilsError
from data_to_paper.run_gpt_code.runtime_issues_collector import RunIssueCollector
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
def _assert_known_mis_imports():
    for name, module in KNOWN_MIS_IMPORTS.items():
        try:
            importlib.import_module(module, name)
        except ImportError:
            raise ImportError(f"Wrong imports in KNOWN_MIS_IMPORTS.\nFailed importing {name} from {module}")


_assert_known_mis_imports()


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
    headers_required_in_code: Tuple[str, ...] = ()

    prompt_to_append_at_end_of_response: str = \
        dedent_triple_quote_str("""
            Please rewrite the complete code again with these issues corrected.
            Even if you are changing just a few lines, you must return the complete code again in a single code block, \
            including the unchanged parts, so that I can just copy-paste and run it.
            {required_headers_prompt}    
        """)
    runner_cls: CodeRunner = CodeRunner

    max_debug_iterations: int = 5
    debug_iteration = 0

    previous_code: Optional[str] = None
    _requesting_small_change: bool = False  # True when USER ask for modifications of an already existing code
    _previous_code_problem: CodeProblem = CodeProblem.NoCode
    gpt_script_filename: str = 'debugger_gpt'

    """
    PROPERTIES
    """

    @property
    def required_headers_prompt(self) -> str:
        if len(self.headers_required_in_code) == 0:
            return ''
        return 'Your code must be enclosed in a single code block and must contain the following sections:\n' + \
               '\n'.join(f'"{header}"' for header in self.headers_required_in_code)

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

    @property
    def description_of_allowed_output_files(self):
        requirements = self.output_file_requirements
        if len(requirements) == 0:
            return 'Your code should not write to any file.'

        return 'Your code should only write to these files: {}.'.format(
            ', '.join(f'"{r.filename}"' for r in requirements)
        )

    """
    ISSUES
    """

    def _get_issue_for_known_mis_imports(self, e: ImportError) -> Optional[RunIssue]:
        if not hasattr(e, 'fromlist'):
            return
        if len(e.fromlist) != 1:
            return
        var = e.fromlist[0]
        if var not in KNOWN_MIS_IMPORTS:
            return
        correct_package = KNOWN_MIS_IMPORTS[var]
        # extract from correct_package up to the first '.':
        package_base = correct_package[:correct_package.index('.')] if '.' in correct_package else correct_package
        if package_base not in self.supported_packages:
            return
        return RunIssue(
            issue=dedent_triple_quote_str("""
                I ran the code and got the following error message:
                ```
                {}
                ```
                """).format(e),
            instructions=dedent_triple_quote_str("""
                Your code should only use these packages: {supported_packages}.
                Note that there is a `{var}` in `{known_package}`. Is this perhaps what you needed? 
                """).format(supported_packages=self.supported_packages, var=var, known_package=KNOWN_MIS_IMPORTS[var]),
            code_problem=CodeProblem.RuntimeError,
            comment='ImportError detected in gpt code',
        )

    def _get_issue_for_allowed_packages(self, error: ImportError) -> Optional[RunIssue]:
        respond_to_known_mis_imports = self._get_issue_for_known_mis_imports(error)
        if respond_to_known_mis_imports:
            return respond_to_known_mis_imports
        return RunIssue(
            issue=dedent_triple_quote_str("""
                I ran the code and got the following error message:
                ```
                {}
                ```
                """).format(error),
            instructions=dedent_triple_quote_str("""
                Your code should only use these packages: {supported_packages}.
                """).format(supported_packages=self.supported_packages),
            code_problem=CodeProblem.RuntimeError,
            comment='ImportError detected in gpt code',
        )

    def _get_issue_for_file_not_found(self, error: FileNotFoundError) -> RunIssue:
        return RunIssue(
            issue=dedent_triple_quote_str("""
                I ran the code and got the following error message:
                ```
                {}
                ```
                """).format(error),
            instructions=dedent_triple_quote_str("""
                As noted in the data description, we only have these files:
                {}  
    
                Note that all input files are located in the same directory as the code. 
                """).format(self.data_filenames),
            code_problem=CodeProblem.RuntimeError,
            comment='FileNotFound detected in code',
        )

    def _get_issue_for_regular_exception_or_warning(self, error: FailedRunningCode,
                                                    code_runner: CodeRunner) -> RunIssue:
        error_message = error.get_traceback_message(code_runner.lines_added_in_front_of_code)
        return RunIssue(
            issue=dedent_triple_quote_str("""
            I ran the code and got the following {} message:
            ```
            {}
            ```
            """).format('warning' if isinstance(error, Warning) else 'error', error_message),
            code_problem=CodeProblem.SyntaxError if isinstance(error, SyntaxError) else CodeProblem.RuntimeError,
            comment='Runtime exception in code',
        )

    def _get_issue_for_timeout(self, error: TimeoutError) -> RunIssue:
        return RunIssue(
            issue="I ran the code, but it just ran forever... Perhaps got stuck in too long calculations.",
            code_problem=CodeProblem.RuntimeError,
            comment='Code has timed out',
        )

    def _get_issue_for_incomplete_code_block(self) -> RunIssue:
        if self.model_engine < MAX_MODEL_ENGINE:
            self.model_engine = self.model_engine.get_next()
            instructions = f"Let's bump you up to {self.model_engine.get_next()} and REGENERATE!"
        else:
            instructions = "Please REGENERATE!"
        return RunIssue(
            issue="Your sent incomplete code.",
            instructions=instructions,
            comment='Code is incomplete',
            end_with='',
            code_problem=CodeProblem.IncompleteBlock,
        )

    def _get_issue_for_missing_or_multiple_code_blocks(self, e: FailedExtractingBlock) -> RunIssue:
        """
        We notify missing or incomplete code to chatgpt.
        If the conversation already has this notification, we regenerate gpt response instead.
        """
        return RunIssue(
            issue=str(e),
            comment='Failed extracting code from gpt response',
            end_with=self.required_headers_prompt,
            code_problem=CodeProblem.NotSingleBlock,
        )

    def _get_issue_for_forbidden_functions(self, error: CodeUsesForbiddenFunctions) -> RunIssue:
        func = error.func
        if func == 'print':
            if not self.output_file_requirements:
                return RunIssue(
                    issue="Please do not use the `print` function.",
                    instructions="Your code should only save new or modified dataframes; should have no other output.",
                    code_problem=CodeProblem.RuntimeError,
                    comment='Code uses `print`'
                )
            else:
                return RunIssue(
                    issue="Please do not use the `print` function.",
                    instructions="The code outputs should be written to the above described output file(s).",
                    code_problem=CodeProblem.RuntimeError,
                    comment='Code uses `print`',
                )
        return RunIssue(
            issue=f"Your code uses the function `{func}`, which is not allowed.",
            code_problem=CodeProblem.RuntimeError,
            comment=f'Code uses forbidden function {func}',
        )

    def _get_issue_for_forbidden_method(self, error: UnAllowedDataframeMethodCall) -> RunIssue:
        func = error.method_name
        return RunIssue(
            issue=f"Your code uses the dataframe method `{func}`, which is not allowed.",
            comment=f'Code uses forbidden method {func}',
            code_problem=CodeProblem.RuntimeError,
        )

    def _get_issue_for_forbidden_import(self, error: CodeImportForbiddenModule) -> RunIssue:
        module = error.module
        return RunIssue(
            issue=f"Your code import the module `{module}`, which is not allowed.",
            instructions="Your code can only use these packages: {supported_packages}.",
            code_problem=CodeProblem.RuntimeError,
            comment='Code imports forbidden module')

    def _get_issues_for_static_code_check(self, code: str) -> List[RunIssue]:
        issues = []
        required_strings_not_found = [s for s in self.headers_required_in_code if s.lower() not in code.lower()]
        if len(required_strings_not_found) > 0:
            issues.append(RunIssue(
                issue=dedent_triple_quote_str("""
                Your code must contain the following sections: 
                {headers_required_in_code}.
                But I could not find these headers:
                {required_strings_not_found}.
                """).format(
                    headers_required_in_code=self.headers_required_in_code,
                    required_strings_not_found=required_strings_not_found,
                ),
                comment='Required sections not found',
                code_problem=CodeProblem.StaticCheck,
                end_with='Please rewrite the complete code again with all the required sections.',
            ))
        return issues

    def _get_issue_for_forbidden_write(self, error: CodeWriteForbiddenFile) -> RunIssue:
        file = error.file
        return RunIssue(
            issue=f'Your code writes to the file "{file}" which is not allowed.',
            instructions=self.description_of_allowed_output_files,
            code_problem=CodeProblem.RuntimeError,
            comment='Code writes to forbidden file',
        )

    def _get_issue_for_un_allowed_files_created(self, error: UnAllowedFilesCreated) -> RunIssue:
        return RunIssue(
            issue=f"Your code creates the following files {error.un_allowed_files} which is not allowed.",
            instructions=self.description_of_allowed_output_files,
            code_problem=CodeProblem.RuntimeError,
            comment='Code created forbidden files',
        )

    def _get_issue_for_forbidden_read(self, error: CodeReadForbiddenFile) -> RunIssue:
        file = error.file
        if file == self.output_filename:
            return RunIssue(
                issue=f'Your code tries reading from the output file "{file}".',
                instructions=dedent_triple_quote_str(f"""
                    The code should create and write to this output file, but should not read from it.
                    The only input files from which we can read the data are: 
                    {self.data_filenames}
                    """),
                code_problem=CodeProblem.RuntimeError,
                comment='Code reads from output file',
            )
        else:
            return RunIssue(
                issue=f'Your code reads from the file "{file}" which is not part of the dataset.',
                instructions=dedent_triple_quote_str("""
                    We only have these files:
                    {}
    
                    Note that all input files are located in the same directory as the code. 
                    """).format(self.data_filenames),
                code_problem=CodeProblem.RuntimeError,
                comment='Code reads from forbidden file',
            )

    def _get_issue_for_dataframe_series_change(self, error: DataFrameSeriesChange) -> RunIssue:
        series = error.changed_series
        return RunIssue(
            issue=f'Your code changes the series "{series}" of your dataframe.',
            instructions=dedent_triple_quote_str("""
                Instead of changing an existing dataframe series, please create a new series, and give it a \
                new sensible name.
                """),
            code_problem=CodeProblem.RuntimeError,
            comment='Code modifies dataframe series')

    def _get_issues_for_output_file_content(self, requirement: ContentOutputFileRequirement,
                                            filename: str, content: str) -> List[RunIssue]:
        issues = []
        issue = None
        if len(content.strip()) == 0:
            # The output file is empty.
            issue = RunIssue(
                issue=f'The code created the output file "{filename}", but the file is just empty!',
                instructions="Please revise the code to make sure it correctly writes to the output file.",
                comment='Output file empty',
                code_problem=CodeProblem.OutputFileContentLevelA,
            )
        if count_number_of_tokens_in_message(content, max(ModelEngine)) > requirement.max_tokens:
            # Created output file is too large.
            issue = RunIssue(
                issue=dedent_triple_quote_str("""
                    The code created the output file "{}", but the file is too long!
    
                    Here, for context, is the beginning of the output:
                    ```output
                    {}
                    ```
                    """).format(filename, extract_to_nearest_newline(content, requirement.max_tokens)),
                instructions="Only sensible-length output should be written to the file.",
                comment='Output file too long',
                code_problem=CodeProblem.OutputFileContentLevelC,
            )
        if issue is not None:
            issues.append(issue)
        return issues

    def _get_issues_for_num_files_created(self, code_and_output: CodeAndOutput) -> List[RunIssue]:
        issues = []
        for requirement in self.output_file_requirements:
            output_files = list(code_and_output.requirements_to_output_files_to_contents[requirement].keys())
            if len(output_files) < requirement.minimal_count:
                # The specified number of output files were not created.
                if requirement.is_wildcard():
                    issue = dedent_triple_quote_str(f"""
                        The code was supposed to create at least {requirement.minimal_count} files \
                        of "{requirement.filename}", \
                        but it only created {len(output_files)} files of this type.
                        """)
                else:
                    issue = dedent_triple_quote_str(f"""
                        The code didn't generate the desired output file ({requirement.filename}).
                        """)
                issues.append(RunIssue(
                    category='Not all required files were created',
                    issue=issue,
                    code_problem=CodeProblem.MissingOutputFiles,
                    comment='Code did not create all required files'
                ))
        return issues

    def _get_issues_for_unsaved_dataframes(self, code_and_output: CodeAndOutput) -> List[RunIssue]:
        dataframe_operations = code_and_output.dataframe_operations
        issues = []
        if self.enforce_saving_altered_dataframes and dataframe_operations.get_read_changed_but_unsaved_ids():
            # Not all changed dataframes were saved to files.
            read_but_unsaved_filenames = dataframe_operations.get_read_filenames_from_ids(
                dataframe_operations.get_read_changed_but_unsaved_ids())
            issues.append(RunIssue(
                category='Any modified dataframe should be saved to a file',
                issue=dedent_triple_quote_str(f"""
                    Your code modifies, but doesn't save, some of the dataframes:
                    {read_but_unsaved_filenames}.
                    """),
                instructions=dedent_triple_quote_str("""
                    The code should use `to_csv` to save any modified dataframe in a new file \
                    in the same directory as the code.
                    """),
                comment='Not all modified dataframes were saved',
                code_problem=CodeProblem.MissingOutputFiles,
            ))
        return issues

    def _get_issues_for_created_output_files(self, code_and_output: CodeAndOutput) -> List[RunIssue]:
        issues = []
        files_to_contents = code_and_output.get_created_content_files_to_contents(is_clean=True)
        for requirement in self.output_file_requirements:
            output_files = list(code_and_output.requirements_to_output_files_to_contents[requirement].keys())
            if isinstance(requirement, ContentOutputFileRequirement):
                for filename in output_files:
                    issues.extend(
                        self._get_issues_for_output_file_content(requirement, filename, files_to_contents[filename]))
        return issues

    def _get_issue_for_new_code_not_being_a_modification_of_old_code(self, new_code: str,
                                                                     old_code: str) -> Optional[RunIssue]:
        if line_count(new_code) < line_count(old_code) * 0.9:
            return RunIssue(
                issue="Your code does not seem to be a modification of the previous code.",
                instructions="Please rewrite the complete code again, making sure that the new code is "
                             "a modification of the old code.",
                comment='Code is not a modification of previous code.',
                end_with='',
                code_problem=CodeProblem.StaticCheck,
            )
        return None

    def _get_issue_for_run_utils_error(self, error: RunUtilsError) -> RunIssue:
        return error.issue

    """
    METHODS FOR RUNNING CODE
    """

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

    def _get_response_count(self) -> int:
        """
        USER: Please write code ...
        ASSISTANT: <code>   # 0
        USER: You have a bug ...
        ASSISTANT: <code>   # 1
        """
        return (len(self.conversation) - self._conversation_len_before_first_response - 1) // 2

    def _post_code_as_fresh(self, code: str, code_problem: Optional[CodeProblem] = None):
        self._rewind_conversation_to_first_response()
        self.apply_append_surrogate_message(
            'Here is the code to perform the requested analysis:\n```python\n{}\n```'.format(code),
            web_conversation_name=None,
            comment='Code is freshly re-posted, as if it was the immediate response.')
        self.previous_code = code
        self._previous_code_problem = code_problem

    def _respond_to_issues(self, issues: Union[RunIssue, List[RunIssue]], code: Optional[str] = None):
        """
        We need to decide on the action:
        - Re-post the code as fresh ("repost")
        - Leave the response as is ("leave")
        - Regenerate the response ("regenerate")
        """
        if isinstance(issues, RunIssue):
            issues = [issues]
        issue_collector = RunIssueCollector(issues)
        code_problem = issue_collector.get_most_severe_problem()

        response_count = self._get_response_count()
        if response_count == 0:
            if code_problem <= CodeProblem.IncompleteBlock:
                action = "regenerate"
            elif code_problem == CodeProblem.NotSingleBlock:
                action = "leave"
            else:
                action = "repost"
        else:
            if code_problem > CodeProblem.StaticCheck:
                action = "repost"
            else:
                action = "regenerate"

        if action == "repost":
            self._post_code_as_fresh(code, code_problem)

        message, comment = issue_collector.get_message_and_comment(end_with=self.prompt_to_append_at_end_of_response)
        self.apply_append_user_message(
            content=message + ('\n\nREGENERATE' if action == "regenerate" else ''),
            comment=self.iteration_str + ': ' + comment,
        )

        if action == "regenerate":
            # To regenerate, we delete the last two messages (assistant message and this just-posted user response):
            self.apply_delete_messages([-2, -1])

        self._requesting_small_change = issue_collector.do_all_issues_request_small_change()

    def _get_code_and_respond_to_issues(self) -> Optional[CodeAndOutput]:
        """
        Get a code from chatgpt, run it and return code and result.
        If the code fails, notify chatgpt and return None.
        """
        response = self.apply_get_and_append_assistant_message(is_code=True, previous_code=self.previous_code).content
        code_runner = self._get_code_runner(response)

        # Try to extract the code:
        try:
            code = code_runner.extract_code()
        except IncompleteBlockFailedExtractingBlock:
            self._respond_to_issues(self._get_issue_for_incomplete_code_block())
            return None
        except FailedExtractingBlock as e:
            self._respond_to_issues(self._get_issue_for_missing_or_multiple_code_blocks(e))
            return None

        # We were able to extract the code. We now statically check the code before running it.
        static_code_check_issues = []
        if self._requesting_small_change:
            static_code_check_issues.append(
                self._get_issue_for_new_code_not_being_a_modification_of_old_code(code, self.previous_code))
        static_code_check_issues.extend(self._get_issues_for_static_code_check(code))

        if static_code_check_issues:
            self._respond_to_issues(static_code_check_issues, code)
            return None

        # Code passes static checks. We can now run the code.
        try:
            code_and_output, issue_collector = code_runner.run_code()
        except FailedRunningCode as e:
            exceptions_to_funcs = {
                ImportError: self._get_issue_for_allowed_packages,
                TimeoutError: self._get_issue_for_timeout,
                UnAllowedFilesCreated: self._get_issue_for_un_allowed_files_created,
                FileNotFoundError: self._get_issue_for_file_not_found,
                CodeUsesForbiddenFunctions: self._get_issue_for_forbidden_functions,
                UnAllowedDataframeMethodCall: self._get_issue_for_forbidden_method,
                CodeImportForbiddenModule: self._get_issue_for_forbidden_import,
                CodeWriteForbiddenFile: self._get_issue_for_forbidden_write,
                CodeReadForbiddenFile: self._get_issue_for_forbidden_read,
                DataFrameSeriesChange: self._get_issue_for_dataframe_series_change,
                RunUtilsError: self._get_issue_for_run_utils_error,
            }
            for e_type, func in exceptions_to_funcs.items():
                if isinstance(e.exception, e_type):
                    run_time_issue = func(e.exception)
                    break
            else:
                run_time_issue = self._get_issue_for_regular_exception_or_warning(e, code_runner)
            self._respond_to_issues(run_time_issue, code)
            return None

        # The code ran without raising exceptions.
        # We now check for issues in the output files as well as issues collected during the run:
        output_issues = []
        output_issues.extend(self._get_issues_for_num_files_created(code_and_output))
        output_issues.extend(self._get_issues_for_unsaved_dataframes(code_and_output))
        output_issues.extend(issue_collector.issues)
        output_issues.extend(self._get_issues_for_created_output_files(code_and_output))

        if output_issues:
            # if the code ran, but output was incorrect, we delete any created files:
            with run_in_directory(self.data_folder):
                for file in code_and_output.get_created_data_files():
                    os.remove(file)
            self._respond_to_issues(output_issues, code)
            return None

        return code_and_output

    def run_debugging(self) -> Optional[CodeAndOutput]:
        """
        Run the debugging process.
        If debugging did not converge to a running code within the max_debug_iterations, return None.
        Otherwise, return the code and output.
        """
        self.initialize_conversation_if_needed()
        for self.debug_iteration in range(1, self.max_debug_iterations + 1):
            code_and_output = self._get_code_and_respond_to_issues()
            if code_and_output is not None:
                return code_and_output
        self.apply_append_user_message(
            "It seems like we are not converging. Let's try again from the start.\n"
            "Please provide a fresh new attempt of the code.", ignore=True)
        self._rewind_conversation_to_first_response()

        return None
