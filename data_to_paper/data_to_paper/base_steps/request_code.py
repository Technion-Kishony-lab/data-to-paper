from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple, Dict, Type, Any, Iterable, NamedTuple, Collection

from data_to_paper.env import SUPPORTED_PACKAGES, HUMAN_EDIT_CODE_REVIEW
from data_to_paper.interactive import PanelNames
from data_to_paper.code_and_output_files.code_and_output import CodeAndOutput
from data_to_paper.run_gpt_code.run_issues import CodeProblem
from data_to_paper.code_and_output_files.output_file_requirements import TextContentOutputFileRequirement, \
    OutputFileRequirements
from data_to_paper.utils import dedent_triple_quote_str
from data_to_paper.utils.nice_list import NiceList
from data_to_paper.utils.replacer import Replacer
from data_to_paper.code_and_output_files.file_view_params import ContentViewPurpose
from data_to_paper.servers.llm_call import get_human_response

from .debugger import DebuggerConverser
from .base_products_conversers import BackgroundProductsConverser
from .exceptions import FailedCreatingProductException
from .request_python_value import PythonDictReviewBackgroundProductsConverser
from .result_converser import Rewind



class CodeReviewPrompt(NamedTuple):
    wildcard_filename: Optional[str]
    # if None, the code review is done on the code itself without looking at the content of the created files
    # if not None, the code review is done on the content of the file(s) that match the wildcard_filename

    individually: bool
    # if True, the code review is done separately for each file that matches the wildcard_filename

    prompt: str
    # use {filename} to include the name of the created file
    # use {file_contents_str} to include the content of the created file(s)

    human_edit: Optional[bool] = None
    # if True, the human can edit the response
    # if False, the response is AI only
    # if None, the human can edit the response only if this is the final review


@dataclass
class RequestIssuesToSolutions(PythonDictReviewBackgroundProductsConverser):
    LLM_PARAMETERS = {'temperature': 0.0}
    value_type: type = Dict[str, str]
    response_to_self_error: str = dedent_triple_quote_str("""
        Your response should include a Python dictionary Dict[str, str], mapping the issues you found (keys), \t
        to suggested solutions (values).
        If you are sure that there are no issues, you should respond with an empty dictionary, `{}`.
        """)
    is_new_conversation: Optional[bool] = False
    rewind_after_getting_a_valid_response: Rewind = Rewind.DELETE_ALL
    default_rewind_for_result_error: Rewind = Rewind.AS_FRESH_CORRECTION


@dataclass
class BaseCodeProductsGPT(BackgroundProductsConverser):
    max_code_revisions: int = 5
    max_code_writing_attempts: int = 2
    max_debug_iterations_per_attempt: int = 12
    background_product_fields_to_hide_during_code_revision: Tuple[str, ...] = ()
    debugger_cls: Type[DebuggerConverser] = DebuggerConverser
    code_and_output_cls: Type[CodeAndOutput] = CodeAndOutput
    supported_packages: Tuple[str, ...] = SUPPORTED_PACKAGES
    additional_contexts: Optional[Dict[str, Any]] = None

    attrs_to_send_to_debugger: Tuple[str, ...] = \
        ('output_file_requirements', 'data_filenames', 'data_folder', 'supported_packages', 'model_engine',
         'additional_contexts')

    revision_round: int = 0

    provided_code: Optional[str] = None

    system_prompt: str = dedent_triple_quote_str("""
        You are a brilliant data scientist. You are writing a Python code to analyze data.
        """)

    goal_noun: str = '{code_name} code'
    goal_verb: str = 'write'
    mission_prompt: str = 'Please write a code to analyze the data.'

    output_file_requirements: OutputFileRequirements = \
        OutputFileRequirements((TextContentOutputFileRequirement('results.txt'),))
    # The name of the file that gpt code is instructed to save the results to.

    code_name: str = ''  # e.g. "data analysis"

    gpt_script_filename: str = 'gpt_code'
    # The base name of the python file in which the code written by gpt is saved.

    present_code_as_fresh: str = dedent_triple_quote_str("""
        Here is the code to perform the analysis.
        {created_file_names_explanation}
        ```python
        {code}
        ```
        """)  # set to None to not present code

    code_review_formatting_instructions: str = dedent_triple_quote_str("""
        Return your choice as a Python Dict[str, str], mapping possible issues to suggested changes in the code.

        If you have no suggestions for improvement, return an empty dict:
        ```python
        {}
        ```
        """)

    # set to () to skip option for revision
    code_review_prompts: Collection[CodeReviewPrompt] = (
        CodeReviewPrompt('*', False, dedent_triple_quote_str("""
            I ran your code. 

            Here is the content of the output file(s) that the code created:

            {file_contents_str}

            Please check if there is anything wrong in these results (like unexpected NaN values, or anything else \t
            that may indicate that code improvements are needed).

            {code_review_formatting_instructions}
            """)
                         ),
    )

    file_review_prompts: Iterable[Tuple[str, str]] = ()  # (wildcard_filename, prompt)

    @property
    def output_filename(self) -> str:
        return self.output_file_requirements.get_single_content_file()

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
            if self.revision_round == self.max_code_revisions:
                break
            if not self._are_further_code_revisions_needed(code_and_output, debugger):
                break
            # delete created files:
            code_and_output.created_files.delete_all_created_files(self.data_folder)
            self.revision_round += 1
        code_and_output.name = self.code_name
        code_and_output.provided_code = self.provided_code
        self._app_request_continue()
        return code_and_output

    def _run_debugger(self, previous_code: Optional[str] = None
                      ) -> Tuple[Optional[CodeAndOutput], Optional[DebuggerConverser]]:
        for attempt in range(self.max_code_writing_attempts):
            # in each attempt, we are resetting the conversation back to this tag:
            revision_and_attempt = f"Revision {self.revision_round + 1}/{self.max_code_revisions} " \
                                   f"(attempt {attempt + 1}/{self.max_code_writing_attempts})"
            self.comment(f'Starting to write and debug code. {revision_and_attempt}.')

            # we now call the debugger that will try to run and provide feedback in multiple iterations:
            debugger = self.debugger_cls.from_(
                self,
                is_new_conversation=False,
                max_debug_iterations=self.max_debug_iterations_per_attempt,
                gpt_script_filename=f"{self.gpt_script_filename}_revision{self.revision_round}_attempt{attempt}",
                background_product_fields_to_hide=(() if self.revision_round == 0
                                                   else self.background_product_fields_to_hide_during_code_revision),
                code_and_output_cls=self.code_and_output_cls,
                previous_code=previous_code,
                previous_code_problem=CodeProblem.NoCode if previous_code is None else CodeProblem.AllOK,
                **{k: getattr(self, k) for k in self.attrs_to_send_to_debugger},
            )
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
                    web_conversation_name=None,
                )
            return code_and_output, debugger
        return None, None

    def _are_further_code_revisions_needed(self, code_and_output: CodeAndOutput, debugger: DebuggerConverser) -> bool:
        """
        Return True/False indicating if the LLM wants to revise the code.
        If true, set the conversation to the state where the user ask the LLM to revise the code.
        """
        specific_attrs_for_code_and_output = self._get_specific_attrs_for_code_and_output(code_and_output)
        prompt_to_append_at_end_of_response = (
            Replacer(debugger, debugger.prompt_to_append_at_end_of_response).format_text())
        for index, (wildcard_filename, individually, code_review_prompt, human_edit) \
                in enumerate(self.code_review_prompts):
            if wildcard_filename is None:
                content_files_to_contents = {None: None}
            else:
                content_files_to_contents = \
                    code_and_output.created_files.get_created_content_files_to_pretty_contents(
                        match_filename=wildcard_filename, content_view=ContentViewPurpose.CODE_REVIEW)
                # TODO: check if less confusing for the LLM if we use pvalue_on_str=OnStr.EPSILON
                if len(content_files_to_contents) == 0:
                    continue
                if not individually:
                    content_files_to_contents = {wildcard_filename: '\n'.join(content_files_to_contents.values())}
            for filename, file_contents_str in content_files_to_contents.items():
                formatted_code_review_prompt = \
                    Replacer(
                        self, code_review_prompt,
                        kwargs=dict(
                            file_contents_str=file_contents_str,
                            filename=filename,
                            **{k: Replacer(self, v).format_text()
                               for k, v in specific_attrs_for_code_and_output.items()},
                        ))
                if not formatted_code_review_prompt:
                    continue
                issues_to_solutions = RequestIssuesToSolutions.from_(
                    self,
                    model_engine=self.model_engine,
                    background_product_fields_to_hide=self.background_product_fields_to_hide_during_code_revision,
                    mission_prompt=formatted_code_review_prompt,
                    app=None,
                ).run_and_get_valid_result(with_review=False)

                termination_phrase = 'Looks good - no changes needed.'
                if issues_to_solutions:
                    ai_issues = '\n\n'.join(f'- {issue}:\n{solution}'
                                            for issue, solution in issues_to_solutions.items())
                    ai_issues += '\n\n- And please fix any other issues that you may find.'
                else:
                    ai_issues = termination_phrase
                if HUMAN_EDIT_CODE_REVIEW and \
                        (human_edit or (human_edit is None and index == len(self.code_review_prompts) - 1)):
                    human_response = self._app_receive_text(
                        PanelNames.FEEDBACK, '',
                        title='Your feedback on code and output.',
                        optional_suggestions={'AI': ai_issues,
                                              'Default': termination_phrase})
                else:
                    human_response = None
                issues = ai_issues if human_response is None else human_response
                if issues and issues != termination_phrase:
                    response = dedent_triple_quote_str("""
                        The code has some issues that need to be fixed:

                        {issues_to_solutions}
                        
                        {prompt_to_append_at_end_of_response}
                        """).format(issues_to_solutions=issues,
                                    prompt_to_append_at_end_of_response=prompt_to_append_at_end_of_response)
                    self.apply_append_user_message(response)
                    return True

        return False
