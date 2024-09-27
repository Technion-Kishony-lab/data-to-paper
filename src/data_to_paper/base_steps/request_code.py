from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple, Dict, Type, Any, NamedTuple, Collection, List

from data_to_paper.types import HumanReviewType
from data_to_paper.env import SUPPORTED_PACKAGES, PAUSE_AT_LLM_FEEDBACK, PAUSE_AT_PROMPT_FOR_LLM_FEEDBACK, \
    AUTO_TERMINATE_AI_REVIEW, JSON_MODE, CODING_MODEL_ENGINE
from data_to_paper.interactive import PanelNames
from data_to_paper.code_and_output_files.code_and_output import CodeAndOutput
from data_to_paper.run_gpt_code.run_issues import CodeProblem
from data_to_paper.code_and_output_files.output_file_requirements import TextContentOutputFileRequirement, \
    OutputFileRequirements
from data_to_paper.text import dedent_triple_quote_str
from data_to_paper.utils.nice_list import NiceList
from data_to_paper.utils.replacer import Replacer, format_value
from data_to_paper.code_and_output_files.file_view_params import ViewPurpose

from data_to_paper.interactive.human_actions import RequestInfoHumanAction
from data_to_paper.interactive.human_review import HumanReviewAppInteractor

from data_to_paper.interactive.symbols import Symbols
from data_to_paper.run_gpt_code.code_runner import CodeRunner
from data_to_paper.run_gpt_code.extract_and_check_code import CodeExtractor, ModifyAndCheckCodeExtractor
from data_to_paper.servers.model_engine import ModelEngine

from .debugger import DebuggerConverser
from .base_products_conversers import BackgroundProductsConverser
from .exceptions import FailedCreatingProductException
from .request_python_value import PythonDictReviewBackgroundProductsConverser
from .result_converser import Rewind


class CodeReviewPrompt(NamedTuple):
    name: Optional[str]

    wildcard_filename: Optional[str]
    # if None, the code review is done on the code itself without looking at the content of the created files
    # if not None, the code review is done on the content of the file(s) that match the wildcard_filename

    individually: bool
    # if True, the code review is done separately for each file that matches the wildcard_filename

    prompt: str

    # use {filename} to include the name of the created file
    # use {file_contents_str} to include the content of the created file(s)

    def get_header(self) -> str:
        header = 'Review'
        if self.name:
            header += f' of {self.name}'
        return header


@dataclass
class RequestIssuesToSolutions(PythonDictReviewBackgroundProductsConverser):
    LLM_PARAMETERS = {'temperature': 0.5}
    value_type: type = Dict[str, List[str]]
    json_mode: bool = JSON_MODE
    your_response_should_be_formatted_as: str = dedent_triple_quote_str("""
        a json object that can be evaluated with `json.loads()` to a Python Dict[str, List[str]].
        mapping each check you have done (keys) to a list of 2 strings, indicating either your concern \t
        ["CONCERN", "<your concern>"] or your assertion that this check is ok ["OK", "<your assertion>"].
        Like this
        ```json
        {
            "<your check>": ["CONCERN", "<your concern>"],
            "<your check>": ["OK", "<your assertion>"]
            "...": ["CONCERN/OK", "..."]
        }
        ```
        """)
    formatting_instructions_for_feedback: str = dedent_triple_quote_str("""
        Please correct your response according to my feedback, and send it again.

        Note that the different checks (dict keys) I have listed above are just examples.
        You should add/remove/modify checks to fit with the specifics of the code we are reviewing.

        Remember, your response should be formatted as {your_response_should_be_formatted_as}
        """)

    is_new_conversation: Optional[bool] = False
    rewind_after_getting_a_valid_response: Rewind = Rewind.DELETE_ALL
    default_rewind_for_result_error: Rewind = Rewind.AS_FRESH_CORRECTION

    def _check_response_value(self, response_value: Any) -> Any:
        # The type and structure of the response is checked in the parent class.
        response_value = super()._check_response_value(response_value)
        for key, (type_, feedback) in response_value.items():
            type_ = type_.upper()
            if type_ not in ('CONCERN', 'OK'):
                self._raise_self_response_error(
                    title='# Invalid value.',
                    error_message=f'The first element of the array should be "CONCERN" or "OK", but got {repr(type_)}.'
                )
            response_value[key] = (type_, feedback)
        return response_value


@dataclass
class BaseCodeProductsGPT(BackgroundProductsConverser, HumanReviewAppInteractor):
    model_engine: ModelEngine = CODING_MODEL_ENGINE
    max_code_revisions: int = 5
    max_code_writing_attempts: int = 2
    max_debug_iterations_per_attempt: int = 12
    background_product_fields_to_hide_during_code_revision: Tuple[str, ...] = ()
    debugger_cls: Type[DebuggerConverser] = DebuggerConverser
    code_and_output_cls: Type[CodeAndOutput] = CodeAndOutput
    code_extractor_cls: Type[CodeExtractor] = ModifyAndCheckCodeExtractor
    code_runner_cls: Type[CodeRunner] = CodeRunner
    supported_packages: Tuple[str, ...] = SUPPORTED_PACKAGES
    headers_required_in_code: Tuple[str, ...] = ()

    revision_round: int = 0

    provided_code: Optional[str] = None

    system_prompt: str = dedent_triple_quote_str("""
        You are a brilliant data scientist. You are writing a Python code to analyze data.
        """)

    goal_noun: str = '{code_name} code'
    goal_verb: str = 'write'
    mission_prompt: str = 'Please write a code to analyze the data.'
    termination_phrase: str = 'No issues found.'

    code_name: str = ''  # e.g. "data analysis"

    present_code_as_fresh: str = dedent_triple_quote_str("""
        Here is the code to perform the analysis.
        {created_file_names_explanation}
        ```python
        {code}
        ```
        """)  # set to None to not present code

    your_response_should_be_formatted_as: str = RequestIssuesToSolutions.your_response_should_be_formatted_as

    code_review_formatting_instructions: str = \
        'Your response should be formatted as {your_response_should_be_formatted_as}.\n' \
        'Do NOT provide any corrected code or code fragments.'

    code_review_notes: str = dedent_triple_quote_str("""
        Notes:
        (1) Generalize. 
        The points above are just examples, provided as a basis from which you can generalize to checks \t
        relevant to our specific code.
        (2) Skip irrelevant points. 
        If any of the points above are not applicable, you can skip them.
        (3) Add more checks.
        You can also add as many other relevant checks, both positive ("OK", "...") and negative ("CONCERN", "...").
        (4) Be specific.
        Be specific in the description of the checks (keys) and assessment (values), so that it is clear \t
        what you are referring to in the code.
        """)

    # set to () to skip option for revision
    code_review_prompts: Collection[CodeReviewPrompt] = (
        CodeReviewPrompt(None, '*', False, dedent_triple_quote_str("""
            I ran your code. 

            Here is the content of the output file(s) that the code created:

            {file_contents_str}

            Please check if there is anything wrong in these results (like unexpected NaN values, or anything else \t
            that may indicate that code improvements are needed).

            {code_review_formatting_instructions}

            For example:
            ```python
            {
                "NaN values in the output file":
                    ("CONCERN", "The output contains NaN values in ..."),
                "Output file should be self-contained":
                    ("CONCERN", "A header is missing for ..."),
                "Output file should contain all the required analysis": 
                    ("OK", "Nothing is missing"),
                "Sensible results": 
                    ("CONCERN", "The average of ... does not make sense"),
                "<Any other issues you find>":
                    ("CONCERN", "<Issue description>"),
                "<Any other point you checked and asserted is OK>":
                    ("OK", "<Assertion description>"),
            }
            ```

            {code_review_notes}
            """)),
    )

    _output_file_requirements: OutputFileRequirements = None

    def _create_output_file_requirements(self) -> OutputFileRequirements:
        return OutputFileRequirements((
            TextContentOutputFileRequirement('results.txt'),
        ))

    @property
    def output_file_requirements(self) -> OutputFileRequirements:
        if self._output_file_requirements is None:
            self._output_file_requirements = self._create_output_file_requirements()
        return self._output_file_requirements

    @property
    def requested_output_filenames(self):
        return self.output_file_requirements.get_all_allowed_created_filenames()

    def _get_additional_contexts(self) -> Optional[Dict[str, Any]]:
        return None

    def get_created_file_names_explanation(self, code_and_output: CodeAndOutput) -> str:  # noqa
        created_files = code_and_output.created_files.get_all_created_files()
        if len(created_files) == 0:
            return ''
        elif len(created_files) == 1:
            created_file = next(iter(created_files))
            return f'It creates the file "{created_file}".'
        else:
            return f'It creates the files: {list(created_files)}.'

    def _get_specific_attrs_for_code_and_output(self, code_and_output: CodeAndOutput) -> Dict[str, str]:
        return {}

    @property
    def data_filenames(self) -> NiceList[str]:
        """
        The names of the files that gpt code can access.
        Need to be overridden by subclasses, to include the names of the data files from Products
        """
        return NiceList([],
                        wrap_with='"',
                        prefix='{} data file[s]: ')

    @property
    def data_folder(self) -> Optional[Path]:
        """
        The folder in which the data files are located.
        Need to be overridden by subclasses, to include the folder of the data files from Products
        """
        return None

    @property
    def _request_code_tag(self):
        return f'code_revision_{self.revision_round}'

    def _get_initial_code_and_output(self) -> CodeAndOutput:  # noqa
        return CodeAndOutput()

    def get_code_and_output(self) -> Optional[CodeAndOutput]:
        self.initialize_conversation_if_needed()
        code_and_output = self._get_initial_code_and_output()
        while True:
            code_and_output, debugger = self._run_debugger(code_and_output.code)
            if code_and_output is None:
                raise FailedCreatingProductException("Code debugging failed.")
            if self._get_code_review(code_and_output, debugger):
                break
            # delete created files:
            code_and_output.created_files.delete_all_created_files(self.data_folder)
            self.revision_round += 1
        code_and_output.name = self.code_name
        code_and_output.provided_code = format_value(self, self.provided_code)
        return code_and_output

    def get_debugger(self, previous_code: Optional[str] = None,
                     data_filenames: Optional[Collection[str]] = 'not_provided',
                     data_folder: Optional[Path] = 'not_provided',
                     is_new_conversation: Optional[bool] = 'not_provided',
                     ) -> DebuggerConverser:
        if data_filenames == 'not_provided':
            data_filenames = self.data_filenames
        if data_folder == 'not_provided':
            data_folder = self.data_folder
        if is_new_conversation == 'not_provided':
            is_new_conversation = False
        return self.debugger_cls.from_(
            self,
            is_new_conversation=is_new_conversation,
            max_debug_iterations=self.max_debug_iterations_per_attempt,
            background_product_fields_to_hide=(() if self.revision_round == 0
                                               else self.background_product_fields_to_hide_during_code_revision),
            code_and_output_cls=self.code_and_output_cls,
            previous_code=previous_code,
            previous_code_problem=CodeProblem.NoCode if previous_code is None else CodeProblem.AllOK,
            code_extractor_cls=self.code_extractor_cls,
            code_runner_cls=self.code_runner_cls,
            output_file_requirements=self.output_file_requirements,
            data_filenames=data_filenames,
            data_folder=data_folder,
            supported_packages=self.supported_packages,
            model_engine=self.model_engine,
            headers_required_in_code=self.headers_required_in_code,
            additional_contexts=self._get_additional_contexts(),
        )

    def _run_debugger(self, previous_code: Optional[str] = None
                      ) -> Tuple[Optional[CodeAndOutput], Optional[DebuggerConverser]]:
        for attempt in range(self.max_code_writing_attempts):
            # in each attempt, we are resetting the conversation back to this tag:
            revision_and_attempt = f"Revision {self.revision_round + 1}/{self.max_code_revisions} " \
                                   f"(attempt {attempt + 1}/{self.max_code_writing_attempts})"
            self.comment(f'Starting to write and debug code. {revision_and_attempt}.')

            # we now call the debugger that will try to run and provide feedback in multiple iterations:
            debugger = self.get_debugger(previous_code)
            code_and_output = debugger.run_debugging()
            if code_and_output is None:
                # debugging failed
                self.comment(f'Debugging failed, {revision_and_attempt}.')
                continue

            if self.present_code_as_fresh:
                # debugging succeeded. we now forge the conversation as if the LLM immediately sent the correct code:
                self._rewind_conversation_to_first_response()
                self.apply_append_surrogate_message(
                    content=Replacer(
                        self, self.present_code_as_fresh,
                        kwargs=dict(
                            code=code_and_output.code,
                            created_file_names_explanation=self.get_created_file_names_explanation(code_and_output),
                        )),
                    comment='Adding the debugged code as if it was the original response.',
                )
            return code_and_output, debugger
        return None, None

    def _get_content_files_to_contents(self, code_and_output: CodeAndOutput, wildcard_filename: str,
                                       individually: bool) -> Dict[str, str]:
        if wildcard_filename is None:
            content_files_to_contents = {None: None}
        else:
            content_files_to_contents = \
                code_and_output.created_files.get_created_content_files_to_pretty_contents(
                    view_purpose=ViewPurpose.CODE_REVIEW, match_filename=wildcard_filename, header_level=3)
            if not individually:
                content_files_to_contents = {wildcard_filename: '\n\n'.join(content_files_to_contents.values())}
        return content_files_to_contents

    @staticmethod
    def _convert_issues_to_messages(issues: Dict[str, Tuple[str, str]], header: str) -> Tuple[str, str, bool]:
        """
        Convert the issues to:
        - llm_msg: a string with the issues that are problems to send to the LLM
        - app_msg: a string with all the issues to present in the app
        - is_all_ok: True if all issues are OK, False if all issues are concerns, None if there are both
        """

        concern_issues = {issue: feedback for issue, (type_, feedback) in issues.items() if type_ != 'OK'}
        is_all_ok = True if not concern_issues else False if len(concern_issues) == len(issues) else None
        llm_msg = f'# {header}\n\n'
        if concern_issues:
            llm_msg += '\n\n'.join(f'## {issue}\n{solution}' for issue, solution in concern_issues.items())
        else:
            llm_msg += 'No issues found.'

        if issues:
            app_msg = '\n'.join(
                f'### {Symbols.get_is_ok_symbol(type_ == "OK")} {issue}\n{feedback}'
                for issue, (type_, feedback) in issues.items())
        else:
            app_msg = f'No issues found.'
        app_msg = f'## {Symbols.get_is_ok_symbol(is_all_ok)} {header}\n{app_msg}'
        return llm_msg, app_msg, is_all_ok

    def _get_llm_code_review(self, code_and_output: CodeAndOutput, auto_terminate: bool) -> str:
        if auto_terminate and self.revision_round >= self.max_code_revisions:
            return self.termination_phrase
        llm_msgs_and_is_issues: List[Tuple[str, bool]] = []
        for index, code_review_prompt in enumerate(self.code_review_prompts):
            content_files_to_contents = self._get_content_files_to_contents(
                code_and_output, code_review_prompt.wildcard_filename, code_review_prompt.individually)
            for filename, file_contents_str in content_files_to_contents.items():
                requester = RequestIssuesToSolutions.from_(
                    self,
                    model_engine=self.model_engine,
                    background_product_fields_to_hide=self.background_product_fields_to_hide_during_code_revision,
                    app=None,
                )
                replacing_kwargs = dict(
                    file_contents_str=file_contents_str,
                    filename=filename,
                    **{k: Replacer(self, v).format_text()
                       for k, v in self._get_specific_attrs_for_code_and_output(code_and_output).items()},
                )
                header = Replacer([self, requester], code_review_prompt.get_header(),
                                  kwargs=replacing_kwargs).format_text()
                formatted_code_review_prompt = \
                    Replacer([self, requester], '## Request ' + header + '\n' + code_review_prompt.prompt,
                             kwargs=replacing_kwargs).format_text()
                self._app_send_prompt(PanelNames.FEEDBACK)
                self._app_send_prompt(PanelNames.FEEDBACK, formatted_code_review_prompt,
                                      sleep_for=PAUSE_AT_PROMPT_FOR_LLM_FEEDBACK, from_md=True)
                requester.mission_prompt = formatted_code_review_prompt
                with self._app_temporarily_set_panel_status(PanelNames.FEEDBACK,
                                                            f"Waiting for LLM {header} ({self.model_engine})"):
                    issues_to_is_ok_and_feedback = requester.run_and_get_valid_result(with_review=False)
                llm_msg, app_msg, is_all_ok = \
                    self._convert_issues_to_messages(issues_to_is_ok_and_feedback, header)
                llm_msgs_and_is_issues.append((llm_msg, is_all_ok is True))
                self._app_send_prompt(PanelNames.FEEDBACK, app_msg, sleep_for=PAUSE_AT_LLM_FEEDBACK, from_md=True)

        if all(is_ok for _, is_ok in llm_msgs_and_is_issues):
            return self.termination_phrase
        return '\n\n\n'.join(llm_msg for llm_msg, is_issues in llm_msgs_and_is_issues)

    def _get_human_code_review(self, llm_review: Optional[str] = None,
                               initial_text: str = '',
                               title: str = 'Human Code Review',
                               ) -> Optional[str]:
        if not self.app:
            return None
        human_review, human_action = self._app_receive_text_and_action(PanelNames.FEEDBACK, initial_text=initial_text,
                                                                       title=title,
                                                                       in_field_instructions=dedent_triple_quote_str("""
                Enter your feedback on code and output.
                Leave blank if no issues.
                """), optional_suggestions={'AI': llm_review, 'Default': ''})
        if isinstance(human_action, RequestInfoHumanAction):
            assert human_action.value == 'AI'
            return None
        return human_review

    def _get_code_review(self, code_and_output: CodeAndOutput,
                         debugger: DebuggerConverser) -> bool:
        """
        Return True/False indicating if the LLM wants to revise the code.
        If true, set the conversation to the state where the user ask the LLM to revise the code.
        """
        if self.actual_human_review == HumanReviewType.NONE:
            # Only LLM code review
            llm_review = self._get_llm_code_review(code_and_output, auto_terminate=True)
            human_review = None
        elif self.actual_human_review == HumanReviewType.LLM_FIRST:
            # LLM code review is performed first and sent for human review
            llm_review = self._get_llm_code_review(code_and_output, auto_terminate=AUTO_TERMINATE_AI_REVIEW)
            human_review = self._get_human_code_review(llm_review)
        elif self.actual_human_review == HumanReviewType.LLM_UPON_REQUEST:
            # LLM code review is requested only if human click "AI" button
            llm_review = None
            human_review = self._get_human_code_review(llm_review)
            if human_review is None:
                llm_review = self._get_llm_code_review(code_and_output, auto_terminate=AUTO_TERMINATE_AI_REVIEW)
                human_review = self._get_human_code_review(llm_review, title='Human Code Review (AI draft provided)',
                                                           initial_text=llm_review)
        else:
            raise ValueError(f'Invalid value for human_review: {self.actual_human_review}')

        review = llm_review if human_review is None else human_review
        is_terminating = not review.strip() or review == self.termination_phrase
        if human_review is None:
            review = review + '\n\n## Other\nPlease fix any other issues that you may find.'

        prompt_to_append_at_end_of_response = \
            Replacer(debugger, debugger.prompt_to_append_at_end_of_response).format_text()
        if not is_terminating:
            response = '# Code review\n' + dedent_triple_quote_str("""
                The code has some issues that need to be fixed:

                {code_review}

                {prompt_to_append_at_end_of_response}
                """).format(code_review=review,
                            prompt_to_append_at_end_of_response=prompt_to_append_at_end_of_response)
            self.apply_append_user_message(response)
        return is_terminating
