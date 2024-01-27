from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple, Dict, Type, Any, Union

from data_to_paper.env import SUPPORTED_PACKAGES
from data_to_paper.run_gpt_code.code_and_output import CodeAndOutput
from data_to_paper.run_gpt_code.run_issues import CodeProblem
from data_to_paper.run_gpt_code.output_file_requirements import TextContentOutputFileRequirement, OutputFileRequirements
from data_to_paper.utils import dedent_triple_quote_str
from data_to_paper.utils.nice_list import NiceList
from data_to_paper.utils.replacer import Replacer, StrOrReplacer
from data_to_paper.conversation.message_designation import RangeMessageDesignation

from .debugger import DebuggerConverser
from .base_products_conversers import BackgroundProductsConverser
from .exceptions import FailedCreatingProductException
from .request_python_value import PythonDictReviewBackgroundProductsConverser
from .result_converser import Rewind, SelfResponseError


@dataclass
class RequestIssuesToSolutions(PythonDictReviewBackgroundProductsConverser):
    CHATGPT_PARAMETERS = {'temperature': 0.0}
    value_type: type = Dict[str, str]

    def _raise_self_response_error(self, error_message: StrOrReplacer, rewind: Rewind = Rewind.ACCUMULATE,
                                   add_iterations: int = 0,
                                   bump_model: bool = False):
        msg = dedent_triple_quote_str("""
                Your response should include a Python dictionary Dict[str, str], mapping the issues you found (keys), \
                to suggested solutions (values).
                If you are sure that there are no issues, you should respond with an empty dictionary, `{}`.
            """)
        raise SelfResponseError(msg, rewind=Rewind.AS_FIRST_CORRECTION, bump_model=bump_model,
                                add_iterations=add_iterations)


@dataclass
class BaseCodeProductsGPT(BackgroundProductsConverser):
    max_code_revisions: int = 5
    max_code_writing_attempts: int = 2
    max_debug_iterations_per_attempt: int = 12
    background_product_fields_to_hide_during_code_revision: Tuple[str, ...] = ()
    debugger_cls: Type[DebuggerConverser] = DebuggerConverser
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
    user_initiation_prompt: str = 'Please write a code to analyze the data.'

    output_file_requirements: OutputFileRequirements = \
        OutputFileRequirements((TextContentOutputFileRequirement('results.txt'), ))
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

    code_review_prompts: Optional[Union[str, Tuple[str]]] = dedent_triple_quote_str("""
        I ran your code. 

        {created_file_contents_explanation}

        Please check if there is anything wrong in these results (like unexpected NaN values, or anything else \
        that may indicate that code improvements are needed).

        Return your choice as a Python Dict[str, str], mapping possible issues to suggested changes in the code.

        If you have no suggestions for improvement, return an empty dict:
        ```python
        {}
        ```` 
        """)  # set to None to skip option for revision

    @property
    def output_filename(self) -> str:
        return self.output_file_requirements.get_single_content_file()

    def get_created_file_names_explanation(self, code_and_output: CodeAndOutput) -> str:
        created_files = code_and_output.created_files.get_all_created_files()
        if len(created_files) == 0:
            return ''
        elif len(created_files) == 1:
            created_file = next(iter(created_files))
            return f'It creates the file "{created_file}".'
        else:
            return f'It creates the files: {list(created_files)}.'

    def get_created_file_contents_explanation(self, code_and_output: CodeAndOutput) -> Optional[str]:
        description = code_and_output.created_files.get_created_content_files_description()
        if len(description) == 0:
            return None
        return f'Here is the content of the output file(s) that the code created:\n\n{description}'

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

    def _get_initial_code_and_output(self) -> CodeAndOutput:
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
                # debugging succeeded. we now forge the conversation as if ChatGPT immediately sent the correct code:
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
        Return True/False indicating if ChatGPT wants to revise the code.
        If true, set the conversation to the state where the user ask ChatGPT to revise the code.
        """
        created_file_contents_explanation = self.get_created_file_contents_explanation(code_and_output)
        code_review_prompts = self.code_review_prompts
        if not code_review_prompts:
            return False
        if isinstance(code_review_prompts, str):
            code_review_prompts = (code_review_prompts, )
        specific_attrs_for_code_and_output = self._get_specific_attrs_for_code_and_output(code_and_output)
        conversation_len = len(self.conversation)
        prompt_to_append_at_end_of_response = Replacer(debugger, debugger.prompt_to_append_at_end_of_response)
        for code_review_prompt in code_review_prompts:
            issues_to_solutions = RequestIssuesToSolutions.from_(
                self,
                model_engine=self.model_engine,
                is_new_conversation=False,
                background_product_fields_to_hide=self.background_product_fields_to_hide_during_code_revision,
                user_initiation_prompt=Replacer(
                    self, code_review_prompt,
                    kwargs=dict(
                        created_file_contents_explanation=created_file_contents_explanation,
                        **{k: Replacer(self, v).format_text() for k, v in specific_attrs_for_code_and_output.items()},
                    )),
            ).run_and_get_valid_result()

            # rewind the conversation to the point where the user asked for a revision:
            self.apply_delete_messages(RangeMessageDesignation.from_(start=conversation_len, end=-1))

            if issues_to_solutions:
                self.apply_append_user_message(dedent_triple_quote_str("""
                    The code has some issues that need to be fixed:

                    {issues_to_solutions}

                    - And please fix any other issues that you may find.

                    {prompt_to_append_at_end_of_response}
                    """).format(issues_to_solutions='\n\n'.join(f'- {issue}:\n{solution}'
                                                                for issue, solution in issues_to_solutions.items()),
                                prompt_to_append_at_end_of_response=prompt_to_append_at_end_of_response))
                return True

        return False
