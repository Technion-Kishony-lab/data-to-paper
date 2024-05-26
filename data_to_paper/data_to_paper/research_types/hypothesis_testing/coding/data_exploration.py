from dataclasses import dataclass, field
from typing import Tuple, Optional, Dict, Any, Collection, List

from data_to_paper.base_steps.request_code import CodeReviewPrompt
from data_to_paper.code_and_output_files.output_file_requirements import OutputFileRequirements, \
    TextContentOutputFileRequirement, NumericTextContentOutputFileRequirement
from data_to_paper.research_types.hypothesis_testing.cast import ScientificAgent
from data_to_paper.research_types.hypothesis_testing.coding.base_code_conversers import BaseScientificCodeProductsGPT
from data_to_paper.research_types.hypothesis_testing.coding.utils import get_additional_contexts
from data_to_paper.research_types.hypothesis_testing.model_engines import get_model_engine_for_class
from data_to_paper.run_gpt_code.run_issues import RunIssue, CodeProblem
from data_to_paper.servers.model_engine import ModelEngine
from data_to_paper.utils import dedent_triple_quote_str
from data_to_paper.utils.nice_list import NiceList


@dataclass(frozen=True)
class EnforceContentOutputFileRequirement(TextContentOutputFileRequirement, NumericTextContentOutputFileRequirement):
    should_keep_file: bool = False
    headers_required_in_output: Tuple[str, ...] = \
        ('# Data Size', '# Summary Statistics', '# Categorical Variables', '# Missing Values')

    def get_issues_for_output_file_content(self, filename: str, content: str) -> List[RunIssue]:
        issues = super().get_issues_for_output_file_content(filename, content)
        if issues:
            return issues

        missing_headers = [header for header in self.headers_required_in_output if header not in content]
        if missing_headers:
            issues.append(RunIssue(
                category='Problem in output file(s)',
                item=filename,
                issue=f'The output file "{filename}" should have the following headers: '
                      f'{NiceList(self.headers_required_in_output, wrap_with="`")}.\n'
                      f'But, these headers are missing: '
                      f'{NiceList(missing_headers, wrap_with="`")}.',
                code_problem=CodeProblem.OutputFileContentLevelA,
            ))

        return issues


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

    supported_packages: Tuple[str, ...] = ('pandas', 'numpy', 'scipy')

    mission_prompt: str = dedent_triple_quote_str("""
        As part of a data-exploration phase, please write a complete short Python code for getting a \t
        first sense of the data. 

        Your code should create an output text file named "{output_filename}", which should \t
        contain a summary of the data.

        The output file should be self-contained; any results you choose to save to this file \t
        should be accompanied with a short header.

        The output file should be formatted as follows:

        ```
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

    code_review_prompts: Collection[CodeReviewPrompt] = (
        CodeReviewPrompt('output file', '*', False, dedent_triple_quote_str("""
        I ran your code.

        Here is the content of the output file that the code created:

        {file_contents_str}

        Please carefully check the Python code and the output for possible issues, and \t
        provide a point-by-point assessment. 
        {code_review_formatting_instructions}

        For example:
        ```python
        {
            "NaN values in the output file":
                ("CONCERN", "The output contains NaN values in ..."),
            "Output file should be self-contained":
                ("CONCERN", "A header is missing for ..."),
            "Output file should contain all the required analysis": 
                ("OK", "Nothing is missing"),
            "Sensible results": 
                ("CONCERN", "The average of ... does not make sense"),
            "<Any other issues you find>":
                ("CONCERN", "<Issue description>"),
            "<Any other point you checked and asserted is OK>":
                ("OK", "<Assertion description>"),
        }
        ```

        {code_review_notes}
        """)),
    )

    def _get_additional_contexts(self) -> Optional[Dict[str, Any]]:
        return get_additional_contexts(allow_dataframes_to_change_existing_series=False,
                                       enforce_saving_altered_dataframes=False)
