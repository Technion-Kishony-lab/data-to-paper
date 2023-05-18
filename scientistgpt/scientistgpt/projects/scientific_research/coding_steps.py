from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from scientistgpt.base_steps import BaseCodeProductsGPT
from scientistgpt.projects.scientific_research.cast import ScientificAgent
from scientistgpt.projects.scientific_research.scientific_products import ScientificProducts
from scientistgpt.utils import dedent_triple_quote_str
from scientistgpt.utils.text_utils import NiceList


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

    output_content_prompt: str = dedent_triple_quote_str("""
        Any results you choose to save to this file should be accompanied with a short text description so that \
        the content of the output file is self-contained, and can be understood even in absence of the Python code.
        """)

    code_mission: str = dedent_triple_quote_str("""
        As part of a data-exploration phase, please write a complete short Python code for getting a \
        first sense of the data. For example, depending on the specific dataset, you might want ot include:

        1. Translation of different units into a common sensible unit
        2. Summary statistics of key variables
        3. List of most common values and abundances of categorical variables (if any) 
        4. Counts of missing values
        5. Any other data exploration analysis you deem relevant
        """)
    requesting_code_explanation_prompt: str = None


@dataclass
class DataAnalysisCodeProductsGPT(BaseScientificCodeProductsGPT):
    user_agent: ScientificAgent = ScientificAgent.Debugger
    conversation_name: str = 'data_analysis_code'
    code_name: str = 'Data Analysis'
    background_product_fields = ['data_file_descriptions', 'data_exploration_code_and_output',
                                 'research_goal', 'analysis_plan']
    gpt_script_filename: str = 'data_analysis_code'
    output_content_prompt: str = dedent_triple_quote_str("""
        All results we may need for a scientific paper should be saved to this text file, including \
        analysis findings, summary statistics, etc.
        """)
    code_mission: str = 'Write a complete short Python code to perform the data analysis plan.'
    requesting_code_explanation_prompt: str = dedent_triple_quote_str("""
        Please explain what your code does. Do not provide a line-by-line explanation, rather provide a \
        high-level explanation of the code in a language suitable for a Methods section of a research \
        paper. Also explain what does the code writes into the "{actual_output_filename}" file.
        """)
