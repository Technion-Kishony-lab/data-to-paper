from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Iterable

from scientistgpt.base_steps import BaseCodeProductsGPT
from scientistgpt.projects.scientific_research.cast import ScientificAgent
from scientistgpt.projects.scientific_research.scientific_products import ScientificProducts
from scientistgpt.utils import dedent_triple_quote_str
from scientistgpt.utils.nice_list import NiceList


@dataclass
class BaseScientificCodeProductsGPT(BaseCodeProductsGPT):
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
    def data_filenames(self) -> NiceList[str]:
        return NiceList(self.products.data_file_descriptions.get_data_filenames(),
                        wrap_with='"',
                        prefix='{} data file[s]: ')

    @property
    def data_folder(self) -> Optional[Path]:
        return Path(self.products.data_file_descriptions.data_folder)


@dataclass
class DataExplorationCodeProductsGPT(BaseScientificCodeProductsGPT):
    user_agent: ScientificAgent = ScientificAgent.DataExplorer
    conversation_name: str = 'data_exploration_code'
    code_name: str = 'Data Exploration'
    background_product_fields = ['data_file_descriptions']
    gpt_script_filename: str = 'data_exploration_code'
    output_filename: str = 'data_exploration.txt'
    allowed_created_files: Iterable[str] = ('*.csv',)
    allow_dataframes_to_change_existing_series = False
    enforce_saving_altered_dataframes: bool = True

    code_requesting_prompt: str = dedent_triple_quote_str("""
        As part of a data-exploration phase, please write a complete short Python code for getting a \
        first sense of the data. 

        Your code should create an output text file named "{actual_output_filename}", which should \
        contain a summary of the data.
        Depending on the specifics of the dataset, you might want to include:

        * Measure of the scale of our data (e.g., number of rows, number of columns)
        * Conversion of numeric values with different units into same-unit values
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

        IMPORTANT: If you create a new dataframe or modify or add any new variables to the original dataframe, 
        you should save the modified/new dataframes in new files.
        """)

    requesting_code_explanation_prompt: str = None


@dataclass
class DataAnalysisCodeProductsGPT(BaseScientificCodeProductsGPT):
    ADDITIONAL_DICT_ATTRS = \
        BaseScientificCodeProductsGPT.ADDITIONAL_DICT_ATTRS \
        | {'description_of_additional_data_files_if_any', 'raw_data_filenames'}

    user_agent: ScientificAgent = ScientificAgent.Debugger
    conversation_name: str = 'data_analysis_code'
    code_name: str = 'Data Analysis'
    background_product_fields = ['data_file_descriptions',
                                 'analysis_plan', 'data_exploration_code_and_output', 'research_goal']
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

    @property
    def raw_data_filenames(self) -> NiceList[str]:
        return NiceList(super().data_filenames, wrap_with='"')

    @property
    def files_created_during_data_exploration(self) -> NiceList[str]:
        if self.products.data_exploration_code_and_output is None:
            return NiceList()
        return NiceList(self.products.data_exploration_code_and_output.get_created_files_beside_output_file(),
                        wrap_with='"', separator='\n', last_separator=None)

    @property
    def data_filenames(self) -> NiceList[str]:
        return NiceList(self.raw_data_filenames + self.files_created_during_data_exploration)

    @property
    def description_of_additional_data_files_if_any(self) -> str:
        if len(self.files_created_during_data_exploration) == 0:
            return ''
        return f'Or you can also use the processed files created above by the data exploration code:\n' \
               f'```\n' \
               f'{self.files_created_during_data_exploration}' \
               f'```\n'
