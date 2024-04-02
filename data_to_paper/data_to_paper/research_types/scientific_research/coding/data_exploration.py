from dataclasses import dataclass, field
from typing import Tuple, Optional, Dict, Any, Iterable

from data_to_paper.code_and_output_files.output_file_requirements import OutputFileRequirements
from data_to_paper.research_types.scientific_research.cast import ScientificAgent
from data_to_paper.research_types.scientific_research.coding.base_code_conversers import BaseScientificCodeProductsGPT
from data_to_paper.research_types.scientific_research.coding.data_analysis import EnforceContentOutputFileRequirement
from data_to_paper.research_types.scientific_research.coding.utils import get_additional_contexts
from data_to_paper.research_types.scientific_research.model_engines import get_model_engine_for_class
from data_to_paper.servers.model_engine import ModelEngine
from data_to_paper.utils import dedent_triple_quote_str


@dataclass
class DataExplorationCodeProductsGPT(BaseScientificCodeProductsGPT):
    code_step: str = 'data_exploration'
    background_product_fields: Tuple[str, ...] = ('all_file_descriptions', )
    user_agent: ScientificAgent = ScientificAgent.DataExplorer
    allow_data_files_from_sections: Tuple[Optional[str]] = (None, )
    model_engine: ModelEngine = \
        field(default_factory=lambda: get_model_engine_for_class(DataExplorationCodeProductsGPT))

    output_file_requirements: OutputFileRequirements = \
        OutputFileRequirements([EnforceContentOutputFileRequirement('data_exploration.txt')])
    additional_contexts: Optional[Dict[str, Any]] = field(
        default_factory=lambda: get_additional_contexts(allow_dataframes_to_change_existing_series=False,
                                                        enforce_saving_altered_dataframes=False))

    supported_packages: Tuple[str, ...] = ('pandas', 'numpy', 'scipy')

    mission_prompt: str = dedent_triple_quote_str("""
        As part of a data-exploration phase, please write a complete short Python code for getting a \t
        first sense of the data. 

        Your code should create an output text file named "{output_filename}", which should \t
        contain a summary of the data.

        The output file should be self-contained; any results you choose to save to this file \t
        should be accompanied with a short header.

        The output file should be formatted as follows:

        ```output
        # Data Size
        <Measure of the scale of our data (e.g., number of rows, number of columns)>

        # Summary Statistics
        <Summary statistics of all or key variables>

        # Categorical Variables
        <As applicable, list here categorical values and their most common values>

        # Missing Values
        <Counts of missing, unknown, or undefined values>
        <As applicable, counts of special numeric values that stand for unknown/undefined if any \t
        (check in the "{all_file_descriptions}" above for any)>

        # <title of other summary you deem relevant, if any>
        <Add any other summary of the data you deem relevant>

        # <etc for any other summary you deem relevant.>
        ```

        If any of the above sections is not applicable, then write "# Not Applicable" under that section.

        If needed, you can use the following packages which are already installed:
        {supported_packages}

        Do not provide a sketch or pseudocode; write a complete runnable code.
        Do not create any graphics, figures or any plots.
        Do not send any presumed output examples.
        """)

    code_review_prompts: Iterable[Tuple[str, bool, str]] = (
        ('*', False, dedent_triple_quote_str("""
        I ran your code.

        Here is the content of the output file that the code created:

        {file_contents_str}

        Please follow these two steps:

        (1) Check the code and the output for any issues, and return a bullet-point response addressing these points:
        * Are there any unexpected NaN values in the output.
        * Can results be understood from the output file? In particular, do we have a short label for each result?
        * Are there any results that are missing. Check that under each header in the output file there is \t
        a corresponding meaningful result (or "Not Applicable" if not applicable).
        * Any other issues you find.

        (2) Based on your assessment above, return a Python Dict[str, str] mapping the issues you have noted \t
        above (dict keys) to specific suggested corrections/improvements in the code (dict values).

        For example:
        ```python
        {
            "The result of the average of variable ... is missing": \t
            "Add the missing calculation of ... to the code.",
            "The average of the variable ... is `Nan`": \t
            "Remove missing values in the calculation."
        }
        ```

        Try to be as specific as possible when describing the issues and proposed fixes.
        Include in the dict as many issues as you find. 
        If there are no issues, and the code and tables are just perfect and need no corrections or enhancements, \t
        then return an empty dict: 
        ```python
        {}
        ```

        Important:
        * Do not return the revised code, only the issues and suggested fixes.
        * If there are no critical issues, then return an empty dict: `{}`.
        * Do not create positive issues that require no change in the code. In particular, do not write \t
        {"No issues found": "No corrections or improvements are needed."}, return an empty dict instead.
        """)),
    )
