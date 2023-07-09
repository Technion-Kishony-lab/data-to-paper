from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Tuple, Dict, Type

from data_to_paper.base_products import DataFileDescription, DataFileDescriptions
from data_to_paper.base_steps import BaseCodeProductsGPT, PythonDictWithDefinedKeysReviewBackgroundProductsConverser, \
    BackgroundProductsConverser, LatexReviewBackgroundProductsConverser
from data_to_paper.base_steps.base_products_conversers import ProductsConverser, ReviewBackgroundProductsConverser
from data_to_paper.base_steps.result_converser import Rewind
from data_to_paper.conversation.actions_and_conversations import ActionsAndConversations
from data_to_paper.latex import extract_latex_section_from_response
from data_to_paper.projects.scientific_research.cast import ScientificAgent
from data_to_paper.projects.scientific_research.scientific_products import ScientificProducts, get_code_name, \
    get_code_agent
from data_to_paper.run_gpt_code.types import CodeAndOutput
from data_to_paper.servers.openai_models import ModelEngine
from data_to_paper.utils import dedent_triple_quote_str
from data_to_paper.utils.nice_list import NiceList, NiceDict
from data_to_paper.utils.replacer import Replacer
from data_to_paper.utils.types import ListBasedSet


@dataclass
class BaseScientificCodeProductsHandler:
    code_step: str = ''  # "data_analysis", "data_exploration", "data_processing"
    products: ScientificProducts = None
    assistant_agent: ScientificAgent = ScientificAgent.Performer
    user_agent: ScientificAgent = None

    actions_and_conversations: ActionsAndConversations = field(default_factory=ActionsAndConversations)
    code_name: str = None
    conversation_name: str = None

    def __post_init__(self):
        if self.conversation_name is None:
            self.conversation_name = f'{self.code_step}_code'
        if self.code_name is None:
            self.code_name = get_code_name(self.code_step)
        if self.user_agent is None:
            self.user_agent = get_code_agent(self.code_step)


@dataclass
class BaseScientificCodeProductsGPT(BaseScientificCodeProductsHandler, BaseCodeProductsGPT):
    allow_data_files_from_sections: Tuple[Optional[str]] = (None, )  # None for the raw data files, () for no data files
    background_product_fields: Tuple[str, ...] = ('all_file_descriptions', 'research_goal', 'analysis_plan')
    gpt_script_filename: str = None

    def __post_init__(self):
        if self.gpt_script_filename is None:
            self.gpt_script_filename = f'{self.code_step}_code'
        BaseScientificCodeProductsHandler.__post_init__(self)
        BaseCodeProductsGPT.__post_init__(self)

    @property
    def files_created_in_prior_stages(self) -> NiceList[str]:
        files = NiceList([], wrap_with='"', separator='\n')
        for section in self.allow_data_files_from_sections:
            if section is None:
                continue
            if section in self.products.codes_and_outputs:
                files += self.products.codes_and_outputs[section].get_created_files_beside_output_file()
        return files

    @property
    def data_filenames(self) -> NiceList[str]:
        return NiceList(self.raw_data_filenames + self.files_created_in_prior_stages)

    @property
    def list_additional_data_files_if_any(self) -> str:
        if len(self.files_created_in_prior_stages) == 0:
            return ''
        return f'\nOr you can also use the processed files created above by the data processing code:\n' \
               f'```\n' \
               f'{self.files_created_in_prior_stages}' \
               f'```\n' \
               f'Important: use the correct version of the data to perform each of the steps. For example, ' \
               f'for descriptive statistics use the original data, for model building use the processed data.'

    @property
    def raw_data_filenames(self) -> NiceList[str]:
        if None in self.allow_data_files_from_sections:
            return NiceList(self.products.data_file_descriptions.get_data_filenames(),
                            wrap_with='"',
                            prefix='{} data file[s]: ')
        return NiceList([], wrap_with='"', prefix='No data files.')

    @property
    def data_folder(self) -> Optional[Path]:
        return Path(self.products.data_file_descriptions.data_folder)


@dataclass
class DataExplorationCodeProductsGPT(BaseScientificCodeProductsGPT):

    code_step: str = 'data_exploration'
    background_product_fields: Tuple[str, ...] = ('all_file_descriptions', )
    user_agent: ScientificAgent = ScientificAgent.DataExplorer
    allow_data_files_from_sections: Tuple[Optional[str]] = (None, )

    output_filename: str = 'data_exploration.txt'
    allowed_created_files: Tuple[str, ...] = ()
    allow_dataframes_to_change_existing_series = False
    enforce_saving_altered_dataframes: bool = False

    supported_packages: Tuple[str, ...] = ('pandas', 'numpy', 'scipy')

    user_initiation_prompt: str = dedent_triple_quote_str("""
        As part of a data-exploration phase, please write a complete short Python code for getting a \
        first sense of the data. 

        Your code should create an output text file named "{output_filename}", which should \
        contain a summary of the data.
        Depending on the specifics of the dataset, you might want to include:

        * Measure of the scale of our data (e.g., number of rows, number of columns)
        * Summary statistics of key variables
        * List of most common values of categorical variables (if any) 
        * Counts of missing, unknown, or undefined values, as well as special numeric values that stand for \
        unknown/undefined (check in the file description above for any).
        * Any other data exploration analysis you deem relevant

        The output file should be self-contained; any results you choose to save to this file \
        should be accompanied with a short text header and indication of units (if any).

        If needed, you can use the following packages which are already installed:
        {supported_packages}

        Do not provide a sketch or pseudocode; write a complete runnable code.
        Do not create any graphics, figures or any plots.
        Do not send any presumed output examples.
        """)

    offer_revision_prompt: str = dedent_triple_quote_str("""
        I ran your code. Here is the content of the output file that it created ("{output_filename}"):
        ```output
        {}
        ```

        Please follow these two steps:

        (1) Check the code and the output for any issues, and return a bullet-point response addressing these points:
        * Are there any unexpected NaN values in the output.
        * Can results be understood from the output file, do we have short headers for each result and \
        do all values have sensible names, etc.
        * Any other issues you find.


        (2) Based on your assessment above, choose one of the following options:

        1. I didn't find any issues with the output that require correcting the code, {'choice': 'ok'}.

        2. The data exploration is not perfect. \
        We should revise the code to better address the above issues, {'choice': 'revise'}.

        Return your choice as a Python Dict[str, str], with either: {'choice': 'ok'} or {'choice': 'revise'}.
        """)  # set to None to skip option for revision


@dataclass
class DataPreprocessingCodeProductsGPT(BaseScientificCodeProductsGPT):

    code_step: str = 'data_preprocessing'
    background_product_fields: Tuple[str, ...] = ('research_goal', 'all_file_descriptions', 'outputs:data_exploration')
    user_agent: ScientificAgent = ScientificAgent.DataPreprocessor
    allow_data_files_from_sections: Tuple[Optional[str]] = (None, 'data_exploration', )
    supported_packages: Tuple[str, ...] = ('pandas', 'numpy', 'scipy', 'imblearn')
    output_filename: str = None
    allowed_created_files: Tuple[str, ...] = ('*.csv',)
    allow_dataframes_to_change_existing_series = False
    enforce_saving_altered_dataframes: bool = True

    user_initiation_prompt: str = dedent_triple_quote_str("""
        As part of a data-preprocessing phase, please write a complete short Python code for getting a \
        cleaned, normalized, same-unit, balanced version of the data, ready for use in following analysis \
        steps that will include statistical tests and/or machine learning models on the processed data.

        Your code should create one or more new csv files containing the preprocessed data, saved with \
        sensible file names.

        Depending on the specifics of the dataset and the goal and hypothesis specified above, \
        you might want to preform the following steps:

        * Dealing with missing values - imputation, deletion, etc.
        * Normalization of numeric values with different units into same-unit values.
        * Scaling numeric values into a common scale (e.g., 0-1) using min-max scaling, z-score, etc.
        * Encoding categorical variables into numeric values (e.g., using one-hot encoding)
        * Balancing the data by under-sampling, over-sampling, or more advanced techniques to deal with class imbalance
        * Any other data preprocessing you deem relevant

        You are not obliged to perform all of the above steps, choose the ones that suits the data and the hypothesis
        we are testing (see research goal above). 

        If needed, you can use the following packages which are already installed:
        {supported_packages}

        Do not provide a sketch or pseudocode; write a complete runnable code.
        Do not create any graphics, figures or any plots.
        """)


@dataclass
class DataAnalysisCodeProductsGPT(BaseScientificCodeProductsGPT):

    code_step: str = 'data_analysis'
    background_product_fields: Tuple[str, ...] = \
        ('data_file_descriptions', 'outputs:data_exploration', 'codes:data_preprocessing',
         'created_files_headers:data_preprocessing', 'research_goal', 'hypothesis_testing_plan', 'tables_names')
    user_agent: ScientificAgent = ScientificAgent.Debugger
    allow_data_files_from_sections: Tuple[Optional[str]] = (None, 'data_exploration', 'data_preprocessing')
    supported_packages: Tuple[str, ...] = ('pandas', 'numpy', 'scipy', 'statsmodels', 'sklearn')

    output_filename: str = 'results.txt'
    allowed_created_files: Tuple[str, ...] = ()
    allow_dataframes_to_change_existing_series: bool = True
    enforce_saving_altered_dataframes: bool = False
    model_engine: ModelEngine = ModelEngine.GPT4

    user_initiation_prompt: str = dedent_triple_quote_str("""
        Write a complete Python code to achieve the research goal specified above.
        
        The code should:

        (1) Load the data from the original data files described above (DESCRIPTION OF THE ORIGINAL DATASET).\
        {list_additional_data_files_if_any}

        (2) Create an output text file named "{output_filename}".
        All the results should be writen to this text file.
        Do not write to any other files.

        (3) Perform any preprocessing steps needed to prepare the data for the analysis.
        For example, as applicable:
        * Dealing with missing, unknown, or undefined values, or with special numeric values that stand for \
        unknown/undefined (check in the file description above for any).
        * Normalization of numeric values with different units into same-unit values.
        * Any other data preprocessing you deem relevant.

        (4) Perform the analysis and appropriate statistical tests needed to directly test our specified hypotheses \
        (see above our Research Goal and our Hypothesis Testing Plan).
        Note that the analysis should account for any relevant confounding variables, as applicable. 

        (5) Create and output the data analysis results that are needed to produce a scientific paper \
        including the data for each of the tables specified above.
        For example: 

        ```output                
        ## General results:
        Report any general numerical values you deem relevant to our research paper.
        For example:
            Total number of observations: xxx
            etc.

        ## Results for a Table on "<table name here>":
        <write here all the data needed for this table>

        ## Results for a Table on "<table name here>":
        <write here all the data needed for this table>

        etc
        ```

        Note:
        * The data produced for each table should be distinct and non-overlapping.
        * Nominal values should be accompanied by a measure of uncertainty (p-value, CI).
        * The output should be self-contained; results should be accompanied with a short text header, \
        values should have sensible names, etc. 
        * As needed, you can use the following packages which are already installed:
        {supported_packages}

        Avoid the following:
        Do not provide a sketch or pseudocode; write a complete runnable code.
        Do not create any graphics, figures or any plots.
        Do not send any presumed output examples.
        """)

    offer_revision_prompt: str = dedent_triple_quote_str("""
        I ran your code. Here is the content of the output file that it created ("{output_filename}"):
        ```output
        {}
        ```

        Considering the scientific tables we want to create ("The Names of the Tables of the Paper", above), \
        please follow these two steps:

        (1) Check the code output for any issues, and return a bullet-point response addressing these points:
        * Unexpected NaN values.
        * Missing results needed for any of the tables.
        * Nominal values are reported together with measure of uncertainty (p-value, CI).
        * Imperfect implementation of statistical tests, like not accounting for confounding variables, etc.
        * Results can be understood from the output file; all values have sensible names, etc.
        * Any other issues you find.


        (2) Based on your assessment above, choose one of the following options:

        1. I didn't find any issues with the output that require correcting the code, {'choice': 'ok'}.

        2. The output does not perfectly provides everything we need for the Tables. \
        We should revise the code to better address the above issues, {'choice': 'revise'}.

        Return your choice as a Python Dict[str, str], with either: {'choice': 'ok'} or {'choice': 'revise'}.
        """)  # set to None to skip option for revision


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
    def output_filename(self):
        return self.code_and_output.output_file


@dataclass
class RequestCodeExplanation(BaseScientificPostCodeProductsHandler, LatexReviewBackgroundProductsConverser):
    goal_noun: str = 'explanation of the {code_name} code'
    background_product_fields: Tuple[str, ...] = ('all_file_descriptions',)
    max_reviewing_rounds: int = 0
    rewind_after_end_of_review: Rewind = Rewind.DELETE_ALL
    rewind_after_getting_a_valid_response: Rewind = Rewind.ACCUMULATE
    should_remove_citations_from_section: bool = True
    section_names: Tuple[str, ...] = ('Code Explanation',)

    def __post_init__(self):
        self.background_product_fields = self.background_product_fields + ('codes:' + self.code_step,)
        BaseScientificPostCodeProductsHandler.__post_init__(self)
        LatexReviewBackgroundProductsConverser.__post_init__(self)

    user_initiation_prompt: str = dedent_triple_quote_str("""
        Please return a triple-backtick Latex Block explaining what the code above does. 
        Do not provide a line-by-line explanation, rather provide a \
        high-level explanation of the code in a language suitable for a Methods section of a research \
        paper. 
        {actual_requesting_output_explanation}
        
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
        Also explain what does the code write into the "{output_filename}" file.    
        """)

    @property
    def actual_requesting_output_explanation(self):
        return self.requesting_output_explanation if self.code_and_output.output_file else ''

    def run_dialog_and_get_valid_result(self):
        result = super().run_dialog_and_get_valid_result()
        return extract_latex_section_from_response(result[0], 'Code Explanation', keep_tags=False)


@dataclass
class ExplainCreatedDataframe(BaseScientificPostCodeProductsHandler, BackgroundProductsConverser):
    goal_noun: str = 'explanation of the files created by the {code_name} code'

    def __post_init__(self):
        self.background_product_fields = self.background_product_fields + ('codes:' + self.code_step,)
        BaseScientificPostCodeProductsHandler.__post_init__(self)
        BackgroundProductsConverser.__post_init__(self)

    user_initiation_prompt: str = None
    background_product_fields: Tuple[str, ...] = ('all_file_descriptions', 'research_goal')
    requesting_explanation_for_a_new_dataframe: str = dedent_triple_quote_str("""
        The code creates a new file named "{dataframe_file_name}", with the following columns: 
        {columns}.

        Explain the content of the file, and how it was derived from the original data. 
        Importantly: do NOT explain the content of columns that are already explained for the \
        original dataset (see above DESCRIPTION OF THE DATASET).
        """)

    requesting_explanation_for_a_modified_dataframe: str = dedent_triple_quote_str("""
        Explain the content of all the new or modified columns of "{dataframe_file_name}".

        Return your explanation as a dictionary, where the keys are the column names {columns}, and the values are the \
        strings that explain the content of each column.

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
                    user_initiation_prompt=Replacer(self, self.requesting_explanation_for_a_new_dataframe,
                                                    kwargs={'dataframe_file_name': saved_df_filename,
                                                            'columns': list(columns)}),
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
                    is_new_conversation=False,
                    max_reviewing_rounds=0,
                    rewind_after_end_of_review=Rewind.DELETE_ALL,
                    rewind_after_getting_a_valid_response=Rewind.ACCUMULATE,
                    requested_keys=columns,
                    goal_noun='dictionary that explains the columns of the dataframe',
                    user_initiation_prompt=Replacer(self,
                                                    self.requesting_explanation_for_a_modified_dataframe,
                                                    kwargs={'dataframe_file_name': saved_df_filename,
                                                            'columns': list(columns)}),
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


CODE_STEP_TO_CLASS = {
    'data_exploration': DataExplorationCodeProductsGPT,
    'data_preprocessing': DataPreprocessingCodeProductsGPT,
    'data_analysis': DataAnalysisCodeProductsGPT,
}


@dataclass
class RequestCodeProducts(BaseScientificCodeProductsHandler, ProductsConverser):
    EXPLAIN_CODE_CLASS = RequestCodeExplanation
    EXPLAIN_CREATED_FILES_CLASS = ExplainCreatedDataframe

    @property
    def code_writing_class(self) -> Type[BaseScientificCodeProductsGPT]:
        cls = CODE_STEP_TO_CLASS[self.code_step]
        assert cls.code_step == self.code_step
        return cls

    def get_code_and_output(self) -> CodeAndOutput:
        return self.code_writing_class.from_(self).get_code_and_output()

    def _get_description_of_created_files(self) -> Optional[DataFileDescriptions]:
        return self.EXPLAIN_CREATED_FILES_CLASS.from_(
            self,
            is_new_conversation=None,
            code_step=self.code_step,
            products=self.products,
            actions_and_conversations=self.actions_and_conversations,
        ).ask_for_created_files_descriptions()

    def _get_code_explanation(self) -> str:
        return self.EXPLAIN_CODE_CLASS.from_(
            self,
            is_new_conversation=None,
            code_step=self.code_step,
            products=self.products,
            actions_and_conversations=self.actions_and_conversations,
        ).run_dialog_and_get_valid_result()

    def get_code_and_output_and_descriptions(
            self, with_file_descriptions: bool = True, with_code_explanation: bool = True) -> CodeAndOutput:
        code_and_output = self.get_code_and_output()
        self.products.codes_and_outputs[self.code_step] = code_and_output
        if with_code_explanation:
            code_and_output.code_explanation = self._get_code_explanation()
        if with_file_descriptions and code_and_output.get_created_files_beside_output_file():
            code_and_output.description_of_created_files = self._get_description_of_created_files()
        return code_and_output
