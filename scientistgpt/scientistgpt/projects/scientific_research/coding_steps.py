from dataclasses import dataclass
from pathlib import Path
from typing import Optional

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
    allow_creating_files: bool = True

    output_content_prompt: str = dedent_triple_quote_str("""
        The output file should be self-contained: any results you choose to save to this file \
        should be accompanied with a short text explaining what they represent, and their \
        respective units, if any.
        
        If you modify or add any new variables to the raw data, you should save the modified
        dataset in a new file.
        """)

    code_mission: str = dedent_triple_quote_str("""
        As part of a data-exploration phase, please write a complete short Python code for getting a \
        first sense of the data. For example, depending on the specific dataset, you might want to include:

        * Measure of data scale (e.g., number of rows, number of columns)
        * Translation of different units into a common sensible unit
        * Summary statistics of key variables
        * List of most common values and abundances of categorical variables (if any) 
        * Counts of missing values
        * Any other data exploration analysis you deem relevant
        """)
    requesting_code_explanation_prompt: str = None


@dataclass
class DataAnalysisCodeProductsGPT(BaseScientificCodeProductsGPT):
    ADDITIONAL_DICT_ATTRS = BaseScientificCodeProductsGPT.ADDITIONAL_DICT_ATTRS | {'available_input_files_description'}
    user_agent: ScientificAgent = ScientificAgent.Debugger
    conversation_name: str = 'data_analysis_code'
    code_name: str = 'Data Analysis'
    background_product_fields = ['data_file_descriptions',
                                 'analysis_plan', 'data_exploration_code_and_output', 'research_goal']
    gpt_script_filename: str = 'data_analysis_code'
    output_content_prompt: str = dedent_triple_quote_str("""
        All results we may need for a scientific paper should be saved to this text file, including \
        analysis findings, summary statistics, etc.
        """)
    allow_creating_files: bool = False
        Write a complete short Python code to achieve the goal specified above.
        {available_input_files_description}
        """)
    requesting_code_explanation_prompt: str = dedent_triple_quote_str("""
        Please explain what your code does. Do not provide a line-by-line explanation, rather provide a \
        high-level explanation of the code in a language suitable for a Methods section of a research \
        paper. Also explain what does the code writes into the "{actual_output_filename}" file.
        """)

    @property
    def available_input_files_description(self) -> str:
        if self.products.data_exploration_code_and_output is None:
            return ''

        created_data_files = self.products.data_exploration_code_and_output.get_created_files_beside_output_file()
        if len(created_data_files) == 0:
            return ''
        return f'The following files are available at the code folder:\n' \
               f'The raw data files: {self.data_filenames}.\n' \
               f'The files created by the data exploration code: {created_data_files}.\n'
