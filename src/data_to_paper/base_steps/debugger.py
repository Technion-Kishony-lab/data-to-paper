from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Tuple, Union, Type, Dict, Any, Iterable

import numpy as np

from data_to_paper.env import SUPPORTED_PACKAGES, DEBUG_MODE, MAX_EXEC_TIME, PAUSE_AT_RULE_BASED_FEEDBACK
from data_to_paper.text import dedent_triple_quote_str, line_count, wrap_as_block
from data_to_paper.utils.replacer import format_value
from data_to_paper.utils.print_to_file import print_and_log
from data_to_paper.base_cast import Agent
from data_to_paper.conversation.message_designation import RangeMessageDesignation
from data_to_paper.code_and_output_files.code_and_output import CodeAndOutput
from data_to_paper.code_and_output_files.output_file_requirements import BaseContentOutputFileRequirement, \
    OutputFileRequirements

from data_to_paper.interactive.app_interactor import _raise_if_reset

from data_to_paper.run_gpt_code.run_issues import CodeProblem, RunIssue, RunIssues
from data_to_paper.run_gpt_code.code_runner_wrapper import CodeRunnerWrapper
from data_to_paper.run_gpt_code.code_utils import FailedExtractingBlock, IncompleteBlockFailedExtractingBlock
from data_to_paper.run_gpt_code.exceptions import FailedRunningCode, UnAllowedFilesCreated, \
    CodeUsesForbiddenFunctions, CodeWriteForbiddenFile, CodeReadForbiddenFile, CodeImportForbiddenModule
from data_to_paper.interactive import PanelNames, Symbols
from data_to_paper.run_gpt_code.known_mis_imports import KNOWN_MIS_IMPORTS
from data_to_paper.run_gpt_code.base_run_contexts import RunContext
from data_to_paper.run_gpt_code.code_runner import CodeRunner
from data_to_paper.run_gpt_code.extract_and_check_code import get_issue_for_use_of_a_forbidden_function, CodeExtractor

from .base_products_conversers import BackgroundProductsConverser


def _get_description_of_run_error(error: Exception):
    str_error = str(error)
    if len(str_error) > 2000:
        str_error = str_error[:1000] + '\n[...]\n' + str_error[-800:]
    return dedent_triple_quote_str("""
        I ran the code and got the following error message:
        ```error
        {}
        ```
        """).format(str_error)


# Good for debugging:
FORGIVE_ALL_FORGIVABLE_ISSUES = False


@dataclass
class DebuggerConverser(BackgroundProductsConverser):
    """
    Interact with the LLM to debug a code that needs to create an output file.

    Starting with a conversation which ends with a code-request from the user, DebuggerConverser interacts
    with the LLM to enhance the code until it runs properly and creates a desired output file.

    Interactions with LLM include adequate reporting of:
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
    output_file_requirements: OutputFileRequirements = OutputFileRequirements()

    mission_prompt: str = None
    assistant_agent: Agent = None
    user_agent: Agent = None

    supported_packages: Tuple[str, ...] = SUPPORTED_PACKAGES
    headers_required_in_code: Tuple[str, ...] = ()

    prompt_to_append_at_end_of_response: str = \
        dedent_triple_quote_str("""
            # Instructions:
            Please rewrite the complete code again with these issues corrected.

            # General formatting instructions:
            Even if you are changing just a few lines, you must return the complete code again in a \t
            single code block, including the unchanged parts, so that I can just copy-paste and run it.
            {required_headers_prompt}    
        """)

    max_debug_iterations: int = 5
    debug_iteration = 0
    timeout_sec: int = MAX_EXEC_TIME.val
    code_extractor_cls: Type[CodeExtractor] = CodeExtractor
    code_runner_cls: Type[CodeRunner] = CodeRunner
    additional_contexts: Dict[str, RunContext] = field(default_factory=dict)
    previous_code: Optional[str] = None
    _requesting_small_change: bool = False  # True when USER ask for modifications of an already existing code
    previous_code_problem: CodeProblem = CodeProblem.NoCode
    code_and_output_cls: Type[CodeAndOutput] = CodeAndOutput

    issues_to_counts: Dict[RunIssue, int] = field(default_factory=dict)
    """
    PROPERTIES
    """

    @property
    def required_headers_prompt(self) -> str:
        if len(self.headers_required_in_code) == 0:
            return ''
        return 'Remember, your code must contain the following sections:\n' + \
               '\n'.join(f'"{header}"' for header in self.headers_required_in_code)

    @property
    def iteration_str(self):
        return f'Debug iteration {self.debug_iteration}/{self.max_debug_iterations}'

    @property
    def description_of_allowed_output_files(self):
        requirements = self.output_file_requirements
        if len(requirements) == 0:
            return 'Your code should not write to any file.'

        return 'Your code should only write to these files: {}.'.format(
            ', '.join(f'"{r.generic_filename}"' for r in requirements)
        )

    def _get_allowed_packages(self, contexts) -> str:
        import_context = contexts['ModifyImport']
        return self.supported_packages + import_context.get_custom_imports()

    """
    ISSUES
    """

    def _get_issue_for_known_mis_imports(self, error: ImportError, allowed_packages) -> Optional[RunIssue]:
        if not hasattr(error, 'fromlist'):
            return
        if error.fromlist is None:
            return
        if len(error.fromlist) != 1:
            return
        var = error.fromlist[0]
        if var not in KNOWN_MIS_IMPORTS:
            return
        correct_package = KNOWN_MIS_IMPORTS[var]
        # extract from correct_package up to the first '.':
        package_base = correct_package[:correct_package.index('.')] if '.' in correct_package else correct_package
        if package_base not in self.supported_packages:
            return
        return RunIssue(
            category='Importing packages',
            issue=_get_description_of_run_error(error),
            instructions=dedent_triple_quote_str("""
                Your code should only use these packages: {allowed_packages}.
                Note that there is a `{var}` in `{known_package}`. Is this perhaps what you needed? 
                """).format(allowed_packages=allowed_packages, var=var, known_package=KNOWN_MIS_IMPORTS[var]),
            code_problem=CodeProblem.RuntimeError,
            comment='ImportError detected in gpt code',
        )

    def _get_issue_for_allowed_packages(self, error: ImportError, contexts) -> Optional[RunIssue]:
        allowed_packages = self._get_allowed_packages(contexts)
        respond_to_known_mis_imports = self._get_issue_for_known_mis_imports(error, allowed_packages)
        if respond_to_known_mis_imports:
            return respond_to_known_mis_imports
        return RunIssue(
            category='Importing packages',
            issue=_get_description_of_run_error(error),
            instructions=dedent_triple_quote_str("""
                Your code should only use these packages: {allowed_packages}.
                """).format(allowed_packages=allowed_packages),
            code_problem=CodeProblem.RuntimeError,
            comment='ImportError detected in gpt code',
        )

    def _get_issue_for_file_not_found(self, error: FileNotFoundError, e: FailedRunningCode = None) -> RunIssue:
        return RunIssue(
            category='Available input files',
            issue=_get_description_of_run_error(error),
            instructions=dedent_triple_quote_str("""
                As noted in the data description, we only have these files:
                {}  

                Note that all input files are located in the same directory as the code. 
                """).format(self.data_filenames),
            code_problem=CodeProblem.RuntimeError,
            comment='FileNotFound detected in code',
        )

    def _get_issue_for_regular_exception_or_warning(self, error: FailedRunningCode, num_added_lines: int,
                                                    ) -> RunIssue:
        return RunIssue(
            category='Runtime exception',
            issue=_get_description_of_run_error(error.get_traceback_message(num_added_lines)),
            code_problem=CodeProblem.SyntaxError if isinstance(error, SyntaxError) else CodeProblem.RuntimeError,
            comment='Runtime exception in code',
        )

    def _get_issue_for_timeout(self, error: TimeoutError, e: FailedRunningCode = None) -> RunIssue:
        linenos_lines, msg = e.get_lineno_line_message()
        on_line = '\n'.join(f'On line {lineno}: {line}' for lineno, line in linenos_lines)
        return RunIssue(
            category='Timeout',
            issue=f"I ran the code, but it just ran forever... Perhaps got stuck in too long calculations.\n"
                  f"{on_line}",
            instructions="Anything we can do to make it run faster?",
            code_problem=CodeProblem.TimeoutError,
            comment='Code has timed out',
        )

    def _get_issue_for_incomplete_code_block(self, is_bumped: bool) -> RunIssue:
        if is_bumped:
            instructions = f"Let's bump you up to {self.model_engine} and REGENERATE!"
        else:
            instructions = "Please REGENERATE!"

        return RunIssue(
            category='Code extraction problem',
            issue="Your sent incomplete code.",
            instructions=instructions,
            comment='Code is incomplete',
            end_with='',
            code_problem=CodeProblem.IncompleteBlock,
        )

    def _get_issue_for_missing_or_multiple_code_blocks(self, e: FailedExtractingBlock) -> RunIssue:
        """
        We notify missing or incomplete code to the LLM.
        If the conversation already has this notification, we regenerate gpt response instead.
        """
        return RunIssue(
            category='Code extraction problem',
            issue=str(e),
            comment='Failed extracting code from gpt response',
            end_with=self.required_headers_prompt,
            code_problem=CodeProblem.NotSingleBlock,
        )

    def _get_issue_for_forbidden_functions(self, error: CodeUsesForbiddenFunctions, e: FailedRunningCode = None
                                           ) -> RunIssue:
        func = error.func
        return get_issue_for_use_of_a_forbidden_function(func,
                                                         suggest_print_to_output=bool(self.output_file_requirements))

    def _get_issue_for_forbidden_import(self, error: CodeImportForbiddenModule, e: FailedRunningCode) -> RunIssue:
        module = error.module
        return RunIssue(
            category='Importing packages',
            issue=f"Your code import the module `{module}`, which is not allowed.",
            instructions="Your code can only use these packages: {supported_packages}.",
            code_problem=CodeProblem.RuntimeError,
            comment='Code imports forbidden module')

    def _get_issue_for_forbidden_write(self, error: CodeWriteForbiddenFile, e: FailedRunningCode) -> RunIssue:
        file = error.file
        file_and_ext = Path(file).name
        return RunIssue(
            category='Write to unallowed files',
            issue=f'Your code writes to the file "{file_and_ext}" which is not allowed.',
            instructions=self.description_of_allowed_output_files,
            code_problem=CodeProblem.RuntimeError,
            comment='Code writes to forbidden file',
        )

    def _get_issue_for_un_allowed_files_created(self, error: UnAllowedFilesCreated, e: FailedRunningCode) -> RunIssue:
        return RunIssue(
            category='Wrong output files',
            issue=f"Your code creates the following files {error.un_allowed_files} which is not allowed.",
            instructions=self.description_of_allowed_output_files,
            code_problem=CodeProblem.RuntimeError,
            comment='Code created forbidden files',
        )

    def _get_issue_for_forbidden_read(self, error: CodeReadForbiddenFile, e: FailedRunningCode) -> RunIssue:
        file = error.file
        is_read_file_in_output_file_requirements = len(self.output_file_requirements.get_unmatched_files([file])) == 0
        if is_read_file_in_output_file_requirements:
            return RunIssue(
                category='Wrong input file',
                issue=f'Your code tries reading from the output file "{file}".',
                instructions=dedent_triple_quote_str("""
                    The code can create and write to this output file, but should not read from it.
                    The only input files from which we can read the data are: 
                    {}
                    """).format(self.data_filenames),
                code_problem=CodeProblem.RuntimeError,
                comment='Code reads from output file',
            )
        else:
            return RunIssue(
                category='Wrong input file',
                issue=f'Your code reads from the file "{file}" which is not part of the dataset.',
                instructions=dedent_triple_quote_str("""
                    We only have these files:
                    {}

                    Note that all input files are located in the same directory as the code. 
                    """).format(self.data_filenames),
                code_problem=CodeProblem.RuntimeError,
                comment='Code reads from forbidden file',
            )

    def _get_issues_for_output_file_content(self, requirement: BaseContentOutputFileRequirement,
                                            filename: str, content: str) -> List[RunIssue]:
        return requirement.get_issues_for_output_file_content(filename, content)

    def _get_issues_for_created_output_files(self, code_and_output: CodeAndOutput, contexts) -> List[RunIssue]:
        issues = []
        files_to_contents = code_and_output.created_files.get_created_content_files_to_contents()
        for requirement in self.output_file_requirements:
            if isinstance(requirement, BaseContentOutputFileRequirement):
                for filename in code_and_output.created_files[requirement]:
                    issues.extend(
                        self._get_issues_for_output_file_content(requirement, filename, files_to_contents[filename]))
        return issues

    def _get_issue_for_new_code_not_being_a_modification_of_old_code(self, new_code: str,
                                                                     old_code: str) -> Optional[RunIssue]:
        if line_count(new_code) < line_count(old_code) * 0.9:
            return RunIssue(
                category='New code instead of modifications',
                issue="Your code does not seem to be a modification of the previous code.",
                instructions="Please rewrite the complete code again, making sure that the new code is "
                             "a modification of the old code.",
                comment='Code is not a modification of previous code.',
                end_with='',
                code_problem=CodeProblem.StaticCheck,
            )
        return None

    """
    METHODS FOR RUNNING CODE
    """

    def _bump_to_model_with_more_context(self) -> bool:
        try:
            self.model_engine = self.model_engine.get_model_with_more_context()
            return True
        except ValueError:
            return False

    def _get_code_runner_wrapper(self, code: str) -> CodeRunnerWrapper:
        return CodeRunnerWrapper(
            code=code,
            timeout_sec=self.timeout_sec,
            code_runner=self.get_code_runner(),
        )

    def _get_code_extractor(self) -> CodeExtractor:
        code_extractor = self.code_extractor_cls()
        if self.headers_required_in_code:
            code_extractor.headers_required_in_code = self.headers_required_in_code
        return code_extractor

    def get_code_runner(self) -> CodeRunner:
        return self.code_runner_cls(
            allowed_open_read_files=self.data_filenames,
            output_file_requirements=self.output_file_requirements,
            run_folder=self.data_folder,
            additional_contexts=self.additional_contexts,
        )

    def _get_code_and_output(self, code: str, result: str, created_files: Iterable[str],
                             contexts: Dict[str, Any] = None) -> CodeAndOutput:
        """
        Return the CodeAndOutput object for the given result and created files.
        """
        return self.code_and_output_cls(
            code=code,
            result=result,
            created_files=self.output_file_requirements.convert_to_output_file_requirements_with_content(
                created_files=created_files, run_folder=self.data_folder),
            dataframe_operations=contexts['TrackDataFrames'].dataframe_operations
            if 'TrackDataFrames' in contexts else None,
            contexts=contexts,
        )

    def _get_response_count(self) -> int:
        """
        USER: Please write code ...
        ASSISTANT: <code>   # 0
        USER: You have a bug ...
        ASSISTANT: <code>   # 1
        """
        return (len(self.conversation) - self._conversation_len_before_first_response - 1) // 2

    def _post_code_as_fresh(self, code: str, code_problem: Optional[CodeProblem] = None, action_stage: int = 0):
        self._rewind_conversation_to_first_response(offset=action_stage * 2)
        if action_stage == 0:
            self.previous_code_problem = code_problem
            message = 'Here is the code to perform the requested analysis:'
            comment = 'Code is freshly re-posted, as if it was the FIRST response.'
        elif action_stage == 1:
            message = 'Here is the revised code to perform the requested analysis:'
            comment = 'Code is freshly re-posted, as if it was the SECOND response.'
        else:
            raise ValueError(f'Invalid action_stage: {action_stage}')
        self.previous_code = code

        self.apply_append_surrogate_message(
            content=message + '\n' + wrap_as_block(code, 'python'),
            comment=comment,
        )

    def _remove_issues_exceeding_max_count(self, issues: List[RunIssue]):
        return [issue for issue in issues if issue.forgive_after is None or
                not FORGIVE_ALL_FORGIVABLE_ISSUES and
                self.issues_to_counts.get(issue, 0) < issue.forgive_after]

    def _respond_to_issues(self, issues: Union[None, RunIssue, List[RunIssue], RunIssues],
                           code_and_output: Optional[CodeAndOutput] = None,
                           is_bumped: bool = False
                           ) -> Optional[CodeAndOutput]:
        """
        We post a response to the assistant code, based on the issues.
        We also need to delete (some) of the previous exchange.

        The conversation may have a max of 3 exchanges:

        User: Please write code ... [preexisting request prompt]

        Assistant: <code>   # stage 0
        User: We have a problem ... Please fix.

        Assistant: <code>   # stage 1
        User: You have a bug ...

        Assistant: <code>   # stage 2  [We continue here only if stage 2 was a run-time error]

        In each stage, we need to decide on the action based on the problem in the code:
        - Re-post the code ["repost0" as the original response; "repost1" as the second response]
        - Leave the response as is ("leave")
        - Regenerate ("regen0", "regen1", "regen2": the original response, the second response, the third response)
        """
        if code_and_output and self.app:
            try:
                code_and_output_as_html = code_and_output.as_html()
            except Exception:  # noqa
                pass
            else:
                self._app_send_prompt(PanelNames.PRODUCT, code_and_output_as_html, provided_as_html=True)

        # Get issues
        if issues is None:
            return code_and_output
        if isinstance(issues, RunIssue):
            issues = [issues]
        if not isinstance(issues, RunIssues):
            issues = RunIssues(issues)

        # Get Problem
        problem = issues.get_most_severe_problem()

        # Get Action
        # When we have run_failed, we essentially don't know the quality of the code (e.g. it can be the
        # perfect code with just syntax error, or it can be a code doesn't even create any output files).
        # So run_failed is the only time we allow going from stage 1 to 2.
        # Namely, if we are in stage 2, we had definitely has a run_failed on stage 1.
        plan = np.array((
            # 0              1                   2      <- stage    # Problem           # noqa
            ('regen0',      'regen1',           'regen1'),          # incomplete        # noqa
            ('leave',       'regen1',           'regen2'),          # not_single_block  # noqa
            ('repost0',     'repost0/regen1',   'regen2'),          # static_check      # noqa
            ('repost0',     'repost0/leave',    'repost1'),         # run_failed        # noqa
            ('repost0',     'repost0/leave',    'repost0/regen1'),  # missing_files     # noqa
            ('repost0',     'repost0',          'repost0'),         # run_completed     # noqa
        ))
        #  xxx/yyy: xxx if current problem difficulty is equal or easier to previous_code_problem / else yyy

        current_stage = self._get_response_count()
        action = plan[problem.get_stage(), current_stage]
        if problem.get_stage() == 0 and current_stage == 2:
            assert action == 'regen1'
            if is_bumped:
                action = 'regen2'

        if '/' in action:
            action1, action2 = action.split('/')
            action = action1 if problem.get_stage() >= self.previous_code_problem.get_stage() else action2

        if DEBUG_MODE:
            print_and_log(f'=====================\n'
                          f'current_stage={current_stage}\n'
                          f'      problem={problem}\n'
                          f'prev. problem={self.previous_code_problem}\n'
                          f'       action={action}\n'
                          f'=====================\n', should_log=False)

        if action.startswith("repost") or action.startswith("regen"):
            action_stage = int(action[-1])
            action = action[:-1]
        else:
            action_stage = current_stage

        # Apply Action
        if action == "repost":
            self._post_code_as_fresh(code_and_output.code, problem, action_stage)

        message, comment, posted_issues = issues.get_message_and_comment(
            end_with=format_value(self, self.prompt_to_append_at_end_of_response))
        message += '\n\nREGENERATE' if action == "regenerate" else ''
        with self._app_temporarily_set_panel_status(PanelNames.FEEDBACK):
            self.apply_append_user_message(
                content=message,
                comment=self.iteration_str + ': ' + comment,
                sleep_for=PAUSE_AT_RULE_BASED_FEEDBACK,
            )

        if action == "regen":
            # To regenerate, we delete the required pairs of assistant+user messages
            # (including the last message which is the just-posted user response to current issue).
            posted_issues = []
            self.apply_delete_messages(
                RangeMessageDesignation.from_(start=(action_stage - current_stage - 1) * 2, end=-1),
                comment=f'REGENERATE (back to stage {action_stage})',
            )
            self._requesting_small_change = False
        else:
            self._requesting_small_change = issues.do_all_issues_request_small_change()
        # add posted issues to the counts:
        for issue in posted_issues:
            self.issues_to_counts[issue] = self.issues_to_counts.get(issue, 0) + 1
        return None

    @_raise_if_reset
    def _get_code_and_respond_to_issues(self, response: str) -> Optional[CodeAndOutput]:
        """
        Get a code from the LLM, run it and return code and result.
        If the code fails, notify the LLM and return None.
        """
        # Try to extract the code:
        code_extractor = self._get_code_extractor()
        try:
            code, num_added_lines = code_extractor.get_modified_code_and_num_added_lines(response)
        except IncompleteBlockFailedExtractingBlock:
            is_bumped = self._bump_to_model_with_more_context()
            return self._respond_to_issues(self._get_issue_for_incomplete_code_block(is_bumped), is_bumped=is_bumped)
        except FailedExtractingBlock as e:
            return self._respond_to_issues(self._get_issue_for_missing_or_multiple_code_blocks(e))

        code_runner_wrapper = self._get_code_runner_wrapper(code)
        code_and_output = self.code_and_output_cls(code=code)
        # We were able to extract the code. We now statically check the code before running it.
        static_code_check_issues = []
        if self._requesting_small_change:
            static_code_check_issues.append(
                self._get_issue_for_new_code_not_being_a_modification_of_old_code(code, self.previous_code))
        static_code_check_issues.extend(code_extractor.get_issues_for_static_code_check(code=code))

        if static_code_check_issues:
            return self._respond_to_issues(static_code_check_issues, code_and_output)

        # Code passes static checks. We can now run the code.
        result, created_files, multi_context, exception = code_runner_wrapper.run()
        issues = multi_context.issues
        contexts = multi_context.contexts
        code_and_output = self._get_code_and_output(code, result, created_files, contexts)

        if exception is not None:
            if isinstance(exception, RunIssue):
                run_time_issue = exception
            elif isinstance(exception, ImportError):
                run_time_issue = self._get_issue_for_allowed_packages(exception.exception, contexts)
            else:
                exceptions_to_funcs = {
                    TimeoutError: self._get_issue_for_timeout,
                    UnAllowedFilesCreated: self._get_issue_for_un_allowed_files_created,
                    FileNotFoundError: self._get_issue_for_file_not_found,
                    CodeUsesForbiddenFunctions: self._get_issue_for_forbidden_functions,
                    CodeImportForbiddenModule: self._get_issue_for_forbidden_import,
                    CodeWriteForbiddenFile: self._get_issue_for_forbidden_write,
                    CodeReadForbiddenFile: self._get_issue_for_forbidden_read,
                }
                for e_type, func in exceptions_to_funcs.items():
                    if isinstance(exception.exception, e_type):
                        run_time_issue = func(exception.exception, exception)
                        break
                else:
                    run_time_issue = self._get_issue_for_regular_exception_or_warning(exception, num_added_lines)
            return self._respond_to_issues(run_time_issue, code_and_output)

        # The code ran without raising exceptions.
        # We now check for issues in the output files as well as issues collected during the run:
        output_issues = []
        output_issues.extend(issues)
        output_issues.extend(self._get_issues_for_created_output_files(code_and_output, contexts))
        output_issues = self._remove_issues_exceeding_max_count(output_issues)
        if output_issues:
            # if the code ran, but output was incorrect, we delete any created files:
            code_and_output.created_files.delete_all_created_files(self.data_folder)
            return self._respond_to_issues(output_issues, code_and_output)

        return self._respond_to_issues(None, code_and_output)

    def run_debugging(self) -> Optional[CodeAndOutput]:
        """
        Run the debugging process.
        If debugging did not converge to a running code within the max_debug_iterations, return None.
        Otherwise, return the code and output.
        """
        self.initialize_conversation_if_needed()
        for self.debug_iteration in range(1, self.max_debug_iterations + 1):
            response = self.apply_get_and_append_assistant_message(is_code=True,
                                                                   previous_code=self.previous_code).content
            with self._app_temporarily_set_panel_status(PanelNames.FEEDBACK, 'Running and checking code'):
                self._app_send_prompt(PanelNames.FEEDBACK)
                code_and_output = self._get_code_and_respond_to_issues(response)
            if code_and_output is not None:
                self._app_send_prompt(
                    PanelNames.FEEDBACK,
                    dedent_triple_quote_str(f"""
                    ## {Symbols.CHECK_SYMBOL} Code check successful
                    Code ran without issues and passed all rule-based checks.
                    You can see code output in the Product panel.
                    """),
                    from_md=True,
                    sleep_for=PAUSE_AT_RULE_BASED_FEEDBACK)
                return code_and_output
        self.apply_append_user_message(
            "It seems like we are not converging. Let's try again from the start.\n"
            "Please provide a fresh new attempt of the code.", ignore=True,
            sleep_for=PAUSE_AT_RULE_BASED_FEEDBACK)
        self._rewind_conversation_to_first_response()

        return None
