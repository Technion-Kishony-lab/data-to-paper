from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Tuple

from scientistgpt.conversation.message_designation import RangeMessageDesignation
from scientistgpt.env import SUPPORTED_PACKAGES
from scientistgpt.run_gpt_code.types import CodeAndOutput
from scientistgpt.utils import dedent_triple_quote_str
from scientistgpt.utils.nice_list import NiceList, NiceDict
from scientistgpt.utils.replacer import Replacer
from scientistgpt.utils.types import ListBasedSet
from scientistgpt.base_products import DataFileDescription, DataFileDescriptions
from . import BaseProductsQuotedReviewGPT

from .debugger import DebuggerConverser
from .base_products_conversers import BackgroundProductsConverser
from .exceptions import FailedCreatingProductException
from .request_multi_choice import MultiChoiceBackgroundProductsConverser
from .request_python_value import PythonDictWithDefinedKeysReviewBackgroundProductsConverser
from .result_converser import Rewind


@dataclass
class BaseCodeProductsGPT(BackgroundProductsConverser):
    max_code_revisions: int = 3
    max_code_writing_attempts: int = 2
    max_debug_iterations_per_attempt: int = 12

    supported_packages: Tuple[str] = SUPPORTED_PACKAGES

    allowed_created_files: Tuple[str] = None
    # e.g. ('*.csv', '*.txt'), or `None` for any file.  No need to include the output file, it is added automatically.

    allow_dataframes_to_change_existing_series: bool = True
    enforce_saving_altered_dataframes: bool = False

    revision_round: int = 0

    system_prompt: str = dedent_triple_quote_str("""
        You are a brilliant data scientist. You are writing a Python code to analyze data.
        """)

    goal_noun: str = 'code'
    goal_verb: str = 'write'
    user_initiation_prompt: str = None

    output_filename: str = 'results.txt'
    # The name of the file that gpt code is instructed to save the results to.

    code_name: str = ''  # e.g. "data analysis"

    gpt_script_filename: str = 'gpt_code'
    # The base name of the python file in which the code written by gpt is saved.

    code_requesting_prompt: str = ''

    code_revision_requesting_prompt: str = dedent_triple_quote_str("""
        Revise the code, or just change any key parameters within the code as needed.
        The output of your new code should be a text file named "{actual_output_filename}".
        Send me back the complete revised code.
        Do not just point to what needs to be changed, send the full complete code.
        """)

    present_code_as_fresh: str = dedent_triple_quote_str("""
        Here is the code to perform the analysis.
        {code_save_result_to_file_explanation}
        ```python
        {}
        ```
        """)  # set to None to not present code

    @property
    def code_save_result_to_file_explanation(self) -> str:
        if self.output_filename is None:
            return ''
        return 'It saves results to the file "{actual_output_filename}".'

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
    def actual_output_filename(self):
        if self.revision_round == 0:
            return self.output_filename
        else:
            return self.output_filename.replace('.', f'_revision_{self.revision_round}.')

    @property
    def _request_code_tag(self):
        return f'code_revision_{self.revision_round}'

    def get_code_and_output(self) -> Optional[CodeAndOutput]:
        self.initialize_conversation_if_needed()
        code_and_output = CodeAndOutput()
        while self.revision_round < self.max_code_revisions:
            self._ask_for_code()
            code_and_output = self._run_debugger(code_and_output.code)
            if code_and_output is None:
                raise FailedCreatingProductException()
            if not self._are_further_code_revisions_needed(code_and_output):
                code_and_output.explanation = self._ask_for_code_explanation(code_and_output)
                code_and_output.description_of_created_files = self._ask_for_created_files_descriptions(code_and_output)
                code_and_output.name = self.code_name
                return code_and_output
            self.revision_round += 1
        raise FailedCreatingProductException()

    def _ask_for_code(self):
        self.apply_append_user_message(
            content=self.code_requesting_prompt if self.revision_round == 0 else self.code_revision_requesting_prompt,
            tag=self._request_code_tag)

    def _run_debugger(self, previous_code: Optional[str] = None) -> Optional[CodeAndOutput]:
        start_tag = self._request_code_tag + '_debugging'
        for attempt in range(self.max_code_writing_attempts):
            # in each attempt, we are resetting the conversation back to this tag:
            revision_and_attempt = f"Revision {self.revision_round + 1}/{self.max_code_revisions} " \
                                   f"(attempt {attempt + 1}/{self.max_code_writing_attempts})"
            self.comment(f'Starting to write and debug code. {revision_and_attempt}.', tag=start_tag)

            # we now call the debugger that will try to run and provide feedback in multiple iterations:
            code_and_output = DebuggerConverser.from_(
                self,
                output_filename=self.actual_output_filename,
                data_files=self.data_filenames,
                data_folder=self.data_folder,
                max_debug_iterations=self.max_debug_iterations_per_attempt,
                gpt_script_filename=f"{self.gpt_script_filename}_attempt{attempt}",
                previous_code=previous_code,
                allowed_created_files=self.allowed_created_files,
                allow_dataframes_to_change_existing_series=self.allow_dataframes_to_change_existing_series,
                enforce_saving_altered_dataframes=self.enforce_saving_altered_dataframes,
            ).run_debugging()
            if code_and_output is None:
                # debugging failed
                self.comment(f'Debugging failed, {revision_and_attempt}.')
                continue

            if self.present_code_as_fresh:
                # debugging succeeded. we now forge the conversation as if chatgpt immediately sent the correct code:
                self.apply_delete_messages(
                    message_designation=RangeMessageDesignation.from_(start=start_tag, end=-1),
                    comment='Deleting all debugging correspondence.')
                assert self.conversation[-1].tag == self._request_code_tag

                self.apply_append_surrogate_message(
                    content=Replacer(self, self.present_code_as_fresh, args=(code_and_output.code,)),
                    comment='Adding the debugged code as if it was the original response.',
                    web_conversation_name=None,
                )
            return code_and_output
        return None

    def _are_further_code_revisions_needed(self, code_and_output: CodeAndOutput) -> bool:
        return False

    def _ask_for_code_explanation(self, code_and_output: CodeAndOutput) -> Optional[str]:
        return None

    def _ask_for_created_files_descriptions(self, code_and_output: CodeAndOutput) -> Optional[DataFileDescriptions]:
        return None


@dataclass
class OfferRevisionCodeProductsGPT(BaseCodeProductsGPT):

    requesting_code_explanation_prompt: str = dedent_triple_quote_str("""
        Please explain what your code does. 
        Also explain what does the code writes into the "{actual_output_filename}" file.
        """)  # set to None to skip asking for explanation

    offer_revision_prompt: str = dedent_triple_quote_str("""
        I ran your code. Here is the content of the output file that it created ("{actual_output_filename}"):
        ```
        {}
        ```

        Please check if there is anything wrong in these results (like unexpected NaN values, or anything else
        that may indicate that code improvements are needed), then choose one of the following options:

        1. The results seem reasonable. Let's proceed.

        2. Something is wrong. I need to go back and change/improve the code.

        {choice_instructions}
        """)  # set to None to skip option for revision

    def _ask_for_code_explanation(self, code_and_output: CodeAndOutput) -> Optional[str]:
        if self.requesting_code_explanation_prompt is None:
            return None
        return BaseProductsQuotedReviewGPT.from_(
            self,
            max_reviewing_rounds=0,
            goal_noun='code explanation',
            user_initiation_prompt=self.requesting_code_explanation_prompt,
        ).run_dialog_and_get_valid_result()

    def _are_further_code_revisions_needed(self, code_and_output: CodeAndOutput) -> bool:
        if self.offer_revision_prompt is None:
            return False

        return MultiChoiceBackgroundProductsConverser.from_(
            self,
            user_initiation_prompt=Replacer(self, self.offer_revision_prompt, args=(code_and_output.output,)),
            possible_choices=('1', '2'),
        ).run_and_get_valid_result() == '2'


@dataclass
class DataframeChangingCodeProductsGPT(BaseCodeProductsGPT):
    requesting_explanation_for_a_new_dataframe: str = dedent_triple_quote_str("""
        Explain the content of the file "{dataframe_file_name}", and how the different columns are derived from the \
        original data.
        {quote_request}
        """)

    requesting_explanation_for_a_modified_dataframe: str = dedent_triple_quote_str("""
        Explain the content of all the new or modified columns of "{dataframe_file_name}".

        Return your explanation as a dictionary, where the keys are the column names {columns}, and the values are the \
        strings that explain the content of each column.

        All information you think is important should be encoded in this dictionary. 
        Do not send additional free text beside the text in the dictionary.  
        """)

    def _ask_for_created_files_descriptions(self, code_and_output: CodeAndOutput) -> Optional[DataFileDescriptions]:
        dataframe_operations = code_and_output.dataframe_operations
        data_file_descriptions = DataFileDescriptions(data_folder=self.data_folder)
        saved_ids_filenames = dataframe_operations.get_saved_ids_filenames()
        # sort the saved ids by their filename, so that the order of the questions will be consistent between runs:
        saved_ids_filenames = sorted(saved_ids_filenames, key=lambda saved_id_filename: saved_id_filename[1])

        for saved_df_id, saved_df_filename in saved_ids_filenames:
            read_filename = dataframe_operations.get_read_filename(saved_df_id)
            saved_columns = ListBasedSet(dataframe_operations.get_save_columns(saved_df_id))
            creation_columns = ListBasedSet(dataframe_operations.get_creation_columns(saved_df_id))
            changed_columns = ListBasedSet(dataframe_operations.get_changed_columns(saved_df_id))
            added_columns = saved_columns - creation_columns
            if read_filename is None:
                # this saved dataframe was created by the code, not read from a file
                columns = saved_columns
                response = BaseProductsQuotedReviewGPT.from_(
                    self,
                    max_reviewing_rounds=0,
                    rewind_after_end_of_review=Rewind.DELETE_ALL,
                    goal_noun='the content of the dataframe',
                    user_initiation_prompt=Replacer(self, self.requesting_explanation_for_a_new_dataframe,
                                                    kwargs={'dataframe_file_name': saved_df_filename,
                                                            'columns': columns}),
                ).run_dialog_and_get_valid_result()
                description = f'This csv file was created by the {self.code_name} code.\n' \
                              f'{response}\n'
                data_file_description = DataFileDescription(file_path=saved_df_filename, description=description,
                                                            originated_from=None)
            else:
                # this saved dataframe was read from a file
                columns = added_columns | changed_columns
                columns_to_explanations = PythonDictWithDefinedKeysReviewBackgroundProductsConverser.from_(
                    self,
                    max_reviewing_rounds=0,
                    rewind_after_end_of_review=Rewind.DELETE_ALL,
                    requested_keys=columns,
                    goal_noun='dictionary that explains the columns of the dataframe',
                    user_initiation_prompt=Replacer(self,
                                                    self.requesting_explanation_for_a_modified_dataframe,
                                                    kwargs={
                                                        'dataframe_file_name': saved_df_filename, 'columns': columns}),
                    value_type=Dict[str, str],
                ).run_dialog_and_get_valid_result()

                new_columns_to_explanations = \
                    {column: explanation for column, explanation in columns_to_explanations.items()
                     if column in added_columns}
                modified_columns_to_explanations = \
                    {column: explanation for column, explanation in columns_to_explanations.items()
                        if column not in added_columns}

                if len(modified_columns_to_explanations) > 0:
                    modified_columns_str = f'\nWe modified these columns:\n' \
                                           f'{NiceDict(modified_columns_to_explanations)}\n'
                else:
                    modified_columns_str = ''

                if len(new_columns_to_explanations) > 0:
                    new_columns_str = f'\nWe added these columns:\n' \
                                      f'{NiceDict(new_columns_to_explanations)}\n'
                else:
                    new_columns_str = ''

                description = f'This csv file was created by our {self.code_name} code ' \
                              f'from the file "{read_filename}".\n' \
                              f'{modified_columns_str}' \
                              f'{new_columns_str}'
                data_file_description = DataFileDescription(file_path=saved_df_filename, description=description,
                                                            originated_from=read_filename)

            data_file_descriptions.append(data_file_description)

        return data_file_descriptions
