from dataclasses import dataclass
from typing import Tuple, Optional, Dict, Any

from data_to_paper.code_and_output_files.output_file_requirements import OutputFileRequirements, \
    DataOutputFileRequirement
from data_to_paper.research_types.hypothesis_testing.coding.base_code_conversers import BaseScientificCodeProductsGPT
from data_to_paper.research_types.hypothesis_testing.coding.utils import create_pandas_and_stats_contexts
from data_to_paper.text import dedent_triple_quote_str


@dataclass
class DataPreprocessingCodeProductsGPT(BaseScientificCodeProductsGPT):
    code_step: str = 'data_preprocessing'
    background_product_fields: Tuple[str, ...] = ('research_goal', 'all_file_descriptions', 'outputs:data_exploration')
    # user_agent: ScientificAgent = ScientificAgent.DataPreprocessor
    allow_data_files_from_sections: Tuple[Optional[str]] = (None, 'data_exploration', )
    supported_packages: Tuple[str, ...] = ('pandas', 'numpy', 'scipy', 'imblearn')

    mission_prompt: str = dedent_triple_quote_str("""
        As part of a data-preprocessing phase, please write a complete short Python code for getting a \t
        cleaned, normalized, same-unit, balanced version of the data, ready for use in following analysis \t
        steps that will include statistical tests and/or machine learning models on the processed data.

        Your code should create one or more new csv files containing the preprocessed data, saved with \t
        sensible file names.

        Depending on the specifics of the dataset and the goal and hypothesis specified above, \t
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

    def _create_output_file_requirements(self) -> OutputFileRequirements:
        return OutputFileRequirements([DataOutputFileRequirement('*.csv')])

    def _get_additional_contexts(self) -> Dict[str, Any]:
        return create_pandas_and_stats_contexts(allow_dataframes_to_change_existing_series=False,
                                                enforce_saving_altered_dataframes=True)
