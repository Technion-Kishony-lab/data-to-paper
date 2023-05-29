from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Iterable, Tuple

from scientistgpt.base_steps import BaseCodeProductsGPT, OfferRevisionCodeProductsGPT, DataframeChangingCodeProductsGPT, \
    BaseBackgroundProductsGPT
from scientistgpt.projects.scientific_research.cast import ScientificAgent
from scientistgpt.projects.scientific_research.scientific_products import ScientificProducts
from scientistgpt.utils import dedent_triple_quote_str
from scientistgpt.utils.nice_list import NiceList


@dataclass
class BaseScientificCodeProductsGPT(BaseBackgroundProductsGPT):

    allow_data_files_from_sections: Tuple[Optional[str]] = (None, )  # None for the raw data files

    products: ScientificProducts = None
    background_product_fields = ('data_file_descriptions', 'research_goal', 'analysis_plan')
    conversation_name: str = 'code_debugging'
    assistant_agent: ScientificAgent = ScientificAgent.Performer
    fake_performer_request_for_help: str = \
        "Hi {user_skin_name}, could you please help me write {code_name} code for my project?"
    requesting_code_explanation_prompt: str = dedent_triple_quote_str("""
        Please explain what your code does. Do not provide a line-by-line explanation, rather provide a \
        high-level explanation of the code in a language suitable for a Methods section of a research \
        paper. Also explain what does the code writes into the "{actual_output_filename}" file.
        """)

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
    def description_of_additional_data_files_if_any(self) -> str:
        if len(self.files_created_in_prior_stages) == 0:
            return ''
        return f'Or you can also use the processed files created above by the data exploration code:\n' \
               f'```\n' \
               f'{self.files_created_in_prior_stages}' \
               f'```\n'

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
class DataExplorationCodeProductsGPT(BaseScientificCodeProductsGPT, OfferRevisionCodeProductsGPT):
    user_agent: ScientificAgent = ScientificAgent.DataExplorer
    conversation_name: str = 'data_exploration_code'
    code_name: str = 'Data Exploration'
    background_product_fields = ('data_file_descriptions', )
    gpt_script_filename: str = 'data_exploration_code'
    output_filename: str = 'data_exploration.txt'
    allowed_created_files: Iterable[str] = ()
    allow_dataframes_to_change_existing_series = False
    enforce_saving_altered_dataframes: bool = False

    code_requesting_prompt: str = dedent_triple_quote_str("""
        As part of a data-exploration phase, please write a complete short Python code for getting a \
        first sense of the data. 

        Your code should create an output text file named "{actual_output_filename}", which should \
        contain a summary of the data.
        Depending on the specifics of the dataset, you might want to include:

        * Measure of the scale of our data (e.g., number of rows, number of columns)
        * Summary statistics of key variables
        * List of most common values of categorical variables (if any) 
        * Counts of missing values
        * Any other data exploration analysis you deem relevant

        The output file should be self-contained: any results you choose to save to this file \
        should be accompanied with a short text header and indication of units (if any).

        If needed, you can use the following packages which are already installed:
        {supported_packages}

        Do not provide a sketch or pseudocode; write a complete runnable code.
        Do not create any graphics, figures or any plots.
        Do not send any presumed output examples.
        """)

    requesting_code_explanation_prompt: str = None


@dataclass
class DataPreprocessingCodeProductsGPT(BaseScientificCodeProductsGPT, DataframeChangingCodeProductsGPT):

    allow_data_files_from_sections: Tuple[Optional[str]] = (None, 'data_exploration', )

    user_agent: ScientificAgent = ScientificAgent.DataPreprocessor
    conversation_name: str = 'data_preprocessing_code'
    code_name: str = 'Data Preprocessing'
    background_product_fields = ('data_file_descriptions', 'codes_and_outputs:data_exploration',
                                 'created_files_description:data_exploration')
    gpt_script_filename: str = 'data_preprocessing_code'
    output_filename: str = None
    allowed_created_files: Iterable[str] = ('*.csv',)
    allow_dataframes_to_change_existing_series = False
    enforce_saving_altered_dataframes: bool = True

    code_requesting_prompt: str = dedent_triple_quote_str("""
        As part of a data-preprocessing phase, please write a complete short Python code for getting a \
        cleaned, normalized, balanced version of the data.

        Your code should create one or more new csv files containing the preprocessed data with a sensible file name.

        Depending on the specifics of the dataset, you might want to preform the following steps:

        * Dealing with missing values - imputation, deletion, etc.
        * Normalization of numeric values with different units into same-unit values or into a \
        common scale (e.g., 0-1) using min-max scaling, z-score, etc.
        * Encoding categorical variables into numeric values (e.g., using one-hot encoding)
        * Balancing the data by under-sampling, over-sampling, or more advanced techniques to deal with class imbalance
        * Any other data preprocessing you deem relevant

        If needed, you can use the following packages which are already installed:
        {supported_packages}

        Do not provide a sketch or pseudocode; write a complete runnable code.
        Do not create any graphics, figures or any plots.

        IMPORTANT: If you create a new dataframe or modify or add any new variables to the original dataframe, 
        you should save the modified/new dataframes in new files.
        """)

    requesting_code_explanation_prompt: str = dedent_triple_quote_str("""
        Please explain what your code does. Do not provide a line-by-line explanation, rather provide a \
        high-level explanation of the code in a language suitable for a Methods section of a research \
        paper. Also explain the new dataframes you created and in what way are they different from \
        the original dataframes.
        """)


@dataclass
class DataAnalysisCodeProductsGPT(BaseScientificCodeProductsGPT, OfferRevisionCodeProductsGPT):

    allow_data_files_from_sections: Tuple[Optional[str]] = (None, 'data_exploration', 'data_preprocessing')

    user_agent: ScientificAgent = ScientificAgent.Debugger
    conversation_name: str = 'data_analysis_code'
    code_name: str = 'Data Analysis'
    background_product_fields = \
        ('data_file_descriptions', 'analysis_plan', 'outputs:data_exploration', 'codes:data_preprocessing',
         'research_goal', 'created_files_description:data_exploration', 'created_files_description:data_preprocessing')
    gpt_script_filename: str = 'data_analysis_code'
    output_filename: str = 'results.txt'
    allowed_created_files: Iterable[str] = ()
    allow_dataframes_to_change_existing_series = True
    enforce_saving_altered_dataframes: bool = False

    output_content_prompt: str = dedent_triple_quote_str("""
        All results we may need for a scientific paper should be saved to this text file, including \
        analysis findings, summary statistics, etc.
        """)
    allow_creating_files: bool = False
    code_requesting_prompt: str = dedent_triple_quote_str("""
        Write a complete short Python code to achieve the research goal specified above.

        As input, you can load the following raw data files:
        ```
        {raw_data_filenames}
        ```
        {description_of_additional_data_files_if_any}

        Don't provide a sketch or pseudocode; write a complete runnable code.

        If needed, you can use the following packages which are already installed:
        {supported_packages}

        The output of your code should be a text file named "{actual_output_filename}".
        All results we may need for a scientific paper should be saved to this text file,
        including analysis findings, summary statistics, statistical tests, etc.

        Do not write to any other files.
        Do not create any graphics, figures or any plots.
        Do not send any presumed output examples.
        """)
