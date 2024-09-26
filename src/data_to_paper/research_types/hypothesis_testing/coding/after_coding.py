from dataclasses import dataclass
from typing import Tuple, Optional, Dict, Type

from data_to_paper.base_products.file_descriptions import DataFileDescriptions, DataFileDescription
from data_to_paper.base_steps import LatexReviewBackgroundProductsConverser, BackgroundProductsConverser, \
    ReviewBackgroundProductsConverser, PythonDictWithDefinedKeysReviewBackgroundProductsConverser
from data_to_paper.base_steps.base_products_conversers import ProductsConverser
from data_to_paper.base_steps.result_converser import Rewind
from data_to_paper.code_and_output_files.code_and_output import CodeAndOutput
from data_to_paper.latex import extract_latex_section_from_response
from data_to_paper.latex.latex_doc import LatexDocument

from data_to_paper.research_types.hypothesis_testing.coding.base_code_conversers import \
    BaseScientificCodeProductsHandler, BaseScientificCodeProductsGPT
from data_to_paper.text import dedent_triple_quote_str
from data_to_paper.utils.nice_list import NiceDict
from data_to_paper.utils.replacer import Replacer
from data_to_paper.utils.types import ListBasedSet


@dataclass
class BaseScientificPostCodeProductsHandler(BaseScientificCodeProductsHandler):
    background_product_fields: Tuple[str, ...] = None
    goal_noun: str = '{code_name} code'
    goal_verb: str = 'write'
    max_reviewing_rounds = 0

    def __post_init__(self):
        if self.background_product_fields is None:
            self.background_product_fields = ('all_file_descriptions', f'codes_and_outputs:{self.code_step}',)
        super().__post_init__()

    @property
    def code_and_output(self):
        return self.products.codes_and_outputs[self.code_step]

    @property
    def created_output_filenames(self):
        return self.code_and_output.created_files.get_all_created_files()


@dataclass
class RequestCodeExplanation(BaseScientificPostCodeProductsHandler, LatexReviewBackgroundProductsConverser):
    goal_noun: str = 'explanation of the {code_name} code'
    background_product_fields: Tuple[str, ...] = ('data_file_descriptions',)
    max_reviewing_rounds: int = 0
    rewind_after_end_of_review: Rewind = Rewind.DELETE_ALL
    rewind_after_getting_a_valid_response: Optional[Rewind] = Rewind.ACCUMULATE
    should_remove_citations_from_section: bool = True
    section_names: Tuple[str, ...] = ('Code Explanation',)

    def __post_init__(self):
        self.background_product_fields = self.background_product_fields + ('codes:' + self.code_step,)
        BaseScientificPostCodeProductsHandler.__post_init__(self)
        LatexReviewBackgroundProductsConverser.__post_init__(self)

    mission_prompt: str = dedent_triple_quote_str("""
        Please return a triple-backtick Latex Block explaining what the code above does. 
        Do not provide a line-by-line explanation, rather provide a \t
        high-level explanation of the code in a language suitable for a Methods section of a research \t
        paper.
        Structure the explanation according to the steps of the analysis, and explain the purpose of each step, \t
        and how it was implemented in the code.
        There is no need to explain trivial parts, like reading/writing a file, etc.  

        Your explanation should be written in LaTeX, and should be enclosed within a LaTeX Code Block, like this:

        ```latex
        \\section{Code Explanation}
        <your code explanation here>
        ```

        Remember to enclose your explanation within a LaTeX Code Block, so that I can easily copy-paste it!
        """)

    request_triple_quote_block: Optional[str] = dedent_triple_quote_str("""
        Your code explanation should be enclosed within a triple-backtick "latex" block.
        """)

    requesting_output_explanation: str = dedent_triple_quote_str("""
        Also explain what does the code write into the files(s): {created_output_filenames}.    
        """)

    def run_and_get_valid_result(self):
        result = super().run_and_get_valid_result()
        return extract_latex_section_from_response(result[0], 'Code Explanation', keep_tags=False)


@dataclass
class ExplainCreatedDataframe(BaseScientificPostCodeProductsHandler, BackgroundProductsConverser):
    goal_noun: str = 'explanation of the files created by the {code_name} code'

    def __post_init__(self):
        self.background_product_fields = self.background_product_fields + ('codes:' + self.code_step,)
        BaseScientificPostCodeProductsHandler.__post_init__(self)
        BackgroundProductsConverser.__post_init__(self)

    mission_prompt: str = None
    background_product_fields: Tuple[str, ...] = ('all_file_descriptions', 'research_goal')
    requesting_explanation_for_a_new_dataframe: str = dedent_triple_quote_str("""
        The code creates a new file named "{dataframe_file_name}", with the following columns: 
        {columns}.

        Explain the content of the file, and how it was derived from the original data. 
        Importantly: do NOT explain the content of columns that are already explained for the \t
        original dataset (see above DESCRIPTION OF THE DATASET).
        """)

    requesting_explanation_for_a_modified_dataframe: str = dedent_triple_quote_str("""
        Explain the content of all the new or modified columns of "{dataframe_file_name}".

        Return your explanation as a dictionary, where the keys are the column names {columns}, \t
        and the values are the strings that explain the content of each column.

        All information you think is important should be encoded in this dictionary. 
        Do not send additional free text beside the text in the dictionary.  
        """)

    def ask_for_created_files_descriptions(self) -> Optional[DataFileDescriptions]:
        self.initialize_conversation_if_needed()
        data_folder = self.products.data_file_descriptions.data_folder
        dataframe_operations = self.code_and_output.dataframe_operations
        data_file_descriptions = DataFileDescriptions(data_folder=data_folder)
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
                response = ReviewBackgroundProductsConverser.from_(
                    self,
                    is_new_conversation=False,
                    max_reviewing_rounds=0,
                    rewind_after_end_of_review=Rewind.DELETE_ALL,
                    rewind_after_getting_a_valid_response=Rewind.ACCUMULATE,
                    goal_noun='the content of the dataframe',
                    mission_prompt=Replacer(self, self.requesting_explanation_for_a_new_dataframe,
                                            kwargs={'dataframe_file_name': saved_df_filename,
                                                    'columns': list(columns)}),
                ).run_and_get_valid_result()
                description = f'This csv file was created by the {self.code_name} code.\n' \
                              f'{response}\n'
                data_file_description = DataFileDescription(file_path=saved_df_filename, description=description,
                                                            originated_from=None)
            else:
                # this saved dataframe was read from a file
                columns = added_columns | changed_columns
                columns_to_explanations = PythonDictWithDefinedKeysReviewBackgroundProductsConverser.from_(
                    self,
                    is_new_conversation=False,
                    max_reviewing_rounds=0,
                    rewind_after_end_of_review=Rewind.DELETE_ALL,
                    rewind_after_getting_a_valid_response=Rewind.ACCUMULATE,
                    requested_keys=columns,
                    goal_noun='dictionary that explains the columns of the dataframe',
                    mission_prompt=Replacer(self,
                                            self.requesting_explanation_for_a_modified_dataframe,
                                            kwargs={'dataframe_file_name': saved_df_filename,
                                                    'columns': list(columns)}),
                    value_type=Dict[str, str],
                ).run_and_get_valid_result()

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


@dataclass
class RequestCodeProducts(BaseScientificCodeProductsHandler, ProductsConverser):
    code_writing_class: Type[BaseScientificCodeProductsGPT] = None
    explain_code_class: Optional[Type[RequestCodeExplanation]] = RequestCodeExplanation
    explain_created_files_class: Optional[Type[ExplainCreatedDataframe]] = None
    latex_document: LatexDocument = None

    def _save_code_to_file(self, code_step: str, code_and_output: CodeAndOutput):
        """
        Save the code to a file, only if self.output_directory was defined.
        """
        if self.output_directory is None:
            return
        with open(f'{self.output_directory}/{code_step}.py', 'w', encoding='utf-8') as f:
            f.write(code_and_output.code)

    def get_code_and_output(self) -> CodeAndOutput:
        code_writing = self.code_writing_class.from_(self)
        assert code_writing.code_step == self.code_step
        return code_writing.get_code_and_output()

    def _get_description_of_created_files(self) -> Optional[DataFileDescriptions]:
        return self.explain_created_files_class.from_(
            self,
            is_new_conversation=None,
            conversation_name=self.conversation_name + ' - Created Files',
            code_step=self.code_step,
        ).ask_for_created_files_descriptions()

    def _get_code_explanation(self) -> str:
        return self.explain_code_class.from_(
            self,
            is_new_conversation=None,
            conversation_name=self.conversation_name + ' - Explanation',
            code_step=self.code_step,
        ).run_and_get_valid_result()

    def get_code_and_output_and_descriptions(self) -> CodeAndOutput:
        code_and_output = self.get_code_and_output()
        self.products.codes_and_outputs[self.code_step] = code_and_output
        if self.explain_code_class:
            code_and_output.code_explanation = self._get_code_explanation()
        if self.explain_created_files_class and code_and_output.created_files.get_created_data_files():
            code_and_output.description_of_created_files = self._get_description_of_created_files()
        self._save_code_to_file(self.code_step, code_and_output)
        return code_and_output
