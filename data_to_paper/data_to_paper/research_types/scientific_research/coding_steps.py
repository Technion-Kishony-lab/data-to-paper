from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Tuple, Dict, Type, List, Any

from pandas.core.frame import DataFrame

from data_to_paper.base_products import DataFileDescription, DataFileDescriptions
from data_to_paper.base_steps import BaseCodeProductsGPT, PythonDictWithDefinedKeysReviewBackgroundProductsConverser, \
    BackgroundProductsConverser, LatexReviewBackgroundProductsConverser
from data_to_paper.base_steps.base_products_conversers import ProductsConverser, ReviewBackgroundProductsConverser
from data_to_paper.base_steps.debugger import DebuggerConverser
from data_to_paper.base_steps.result_converser import Rewind
from data_to_paper.conversation.actions_and_conversations import ActionsAndConversations
from data_to_paper.latex import extract_latex_section_from_response
from data_to_paper.latex.latex_doc import LatexDocument

from data_to_paper.research_types.scientific_research.cast import ScientificAgent
from data_to_paper.research_types.scientific_research.scientific_products import ScientificProducts, get_code_name, \
    get_code_agent
from data_to_paper.research_types.scientific_research.table_debugger import TablesDebuggerConverser
from data_to_paper.run_gpt_code.overrides.attr_replacers import PreventAssignmentToAttrs, PreventCalling, AttrReplacer
from data_to_paper.run_gpt_code.overrides.contexts import OverrideStatisticsPackages
from data_to_paper.run_gpt_code.overrides.dataframes import TrackDataFrames
from data_to_paper.run_gpt_code.overrides.pvalue import PValue, is_containing_p_value

from data_to_paper.run_gpt_code.types import CodeAndOutput, TextContentOutputFileRequirement, \
    DataOutputFileRequirement, RunIssue, CodeProblem, NumericTextContentOutputFileRequirement, OutputFileRequirements, \
    PickleContentOutputFileRequirement, RunUtilsError
from data_to_paper.servers.openai_models import ModelEngine, get_model_engine_for_class
from data_to_paper.utils import dedent_triple_quote_str
from data_to_paper.utils.nice_list import NiceList, NiceDict
from data_to_paper.utils.replacer import Replacer
from data_to_paper.utils.types import ListBasedSet
from data_to_paper.research_types.scientific_research.utils_for_gpt_code.utils_modified_for_gpt_use.to_pickle import \
    get_dataframe_to_pickle_attr_replacer, get_pickle_dump_attr_replacer


def _get_additional_contexts(allow_dataframes_to_change_existing_series: bool = False,
                             enforce_saving_altered_dataframes: bool = False,
                             issue_if_statistics_test_not_called: bool = False,
                             ) -> Dict[str, Any]:
    return {
        'TrackDataFrames': TrackDataFrames(
            allow_dataframes_to_change_existing_series=allow_dataframes_to_change_existing_series,
            enforce_saving_altered_dataframes=enforce_saving_altered_dataframes,
        ),
        'OverrideStatisticsPackages': OverrideStatisticsPackages(
            issue_if_statistics_test_not_called=issue_if_statistics_test_not_called),
    }


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
                files += self.products.codes_and_outputs[section].created_files.get_created_data_files()
        return files

    @property
    def data_filenames(self) -> NiceList[str]:
        return NiceList(self.raw_data_filenames + self.files_created_in_prior_stages,
                        wrap_with='"', prefix='\n', separator='\n', suffix='\n')

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
    additional_contexts: Optional[Dict[str, Any]] = field(
        default_factory=lambda: _get_additional_contexts(allow_dataframes_to_change_existing_series=False,
                                                         enforce_saving_altered_dataframes=False))

    supported_packages: Tuple[str, ...] = ('pandas', 'numpy', 'scipy')

    user_initiation_prompt: str = dedent_triple_quote_str("""
        As part of a data-exploration phase, please write a complete short Python code for getting a \
        first sense of the data. 

        Your code should create an output text file named "{output_filename}", which should \
        contain a summary of the data.

        The output file should be self-contained; any results you choose to save to this file \
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
        <As applicable, counts of special numeric values that stand for unknown/undefined if any \
        (check in the "{all_file_descriptions}" above for any)>

        # <other summary you deem relevant, if any>
        <summary>
        ```

        If needed, you can use the following packages which are already installed:
        {supported_packages}

        Do not provide a sketch or pseudocode; write a complete runnable code.
        Do not create any graphics, figures or any plots.
        Do not send any presumed output examples.
        """)

    offer_revision_prompt: str = dedent_triple_quote_str("""
        I ran your code.

        {created_file_contents_explanation}

        Please follow these two steps:

        (1) Check the code and the output for any issues, and return a bullet-point response addressing these points:
        * Are there any unexpected NaN values in the output.
        * Can results be understood from the output file? In particular, do we have a short label for each result?
        * Are there any results that are missing. Check that under each header in the output file there is \
        a corresponding meaningful result.
        * Any other issues you find.

        (2) Based on your assessment above, return a Python Dict[str, str] mapping the issues you have noted \
        above (dict keys) to specific suggested corrections/improvements in the code (dict values).

        For example:
        ```python
        {
            "The result of the average of variable ... is missing": \
            "Add the missing calculation of ... to the code.",
            "The average of the variable <xxx> is `Nan`": \
            "Remove missing values in the calculation."
        }
        ```

        Try to be as specific as possible when describing the issues and proposed fixes.
        Include in the dict as many issues as you find. 
        If there are no issues, and the code and tables are just perfect and need no corrections or enhancements, \
        then return an empty dict: 
        ```python
        {}
        ```

        Important:
        * Do not return the revised code, only the issues and suggested fixes.
        * If there are no critical issues, then return an empty dict: `{}`.
        * Do not create positive issues that require no change in the code. In particular, do not write \
        {"No issues found": "No corrections or improvements are needed."}, return an empty dict instead.

        """)  # set to None to skip option for revision


@dataclass
class DataPreprocessingCodeProductsGPT(BaseScientificCodeProductsGPT):
    code_step: str = 'data_preprocessing'
    background_product_fields: Tuple[str, ...] = ('research_goal', 'all_file_descriptions', 'outputs:data_exploration')
    user_agent: ScientificAgent = ScientificAgent.DataPreprocessor
    allow_data_files_from_sections: Tuple[Optional[str]] = (None, 'data_exploration', )
    supported_packages: Tuple[str, ...] = ('pandas', 'numpy', 'scipy', 'imblearn')

    output_file_requirements: OutputFileRequirements = OutputFileRequirements([DataOutputFileRequirement('*.csv')])
    additional_contexts: Optional[Dict[str, Any]] = field(
        default_factory=lambda: _get_additional_contexts(allow_dataframes_to_change_existing_series=False,
                                                         enforce_saving_altered_dataframes=True))

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
    model_engine: ModelEngine = \
        field(default_factory=lambda: get_model_engine_for_class(DataAnalysisCodeProductsGPT))

    output_file_requirements: OutputFileRequirements = \
        OutputFileRequirements([NumericTextContentOutputFileRequirement('results.txt')])
    additional_contexts: Optional[Dict[str, Any]] = field(
        default_factory=lambda: _get_additional_contexts(allow_dataframes_to_change_existing_series=True,
                                                         enforce_saving_altered_dataframes=False))

    user_initiation_prompt: str = dedent_triple_quote_str("""
        Write a complete Python code to achieve the research goal specified above.

        The code should:

        (1) Load the data from the original data files described above ({data_file_descriptions}).\
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
        (see above our "{research_goal}" and our "{hypothesis_testing_plan}").
        Note that the analysis should account for any relevant confounding variables, as applicable. 

        (5) Create and output the data analysis results that are needed to produce a scientific paper \
        including the data for each of the tables specified above.
        For example: 

        ```output                
        ## General results:
        <Report here any general numerical values you deem relevant to our research paper. For example:>
        <Total number of observations: xxx>
        <Number of groups: yyy>

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
        I ran your code.

        {created_file_contents_explanation}

        Considering the scientific tables we want to create ("{tables_names}", above), \
        please follow these two steps:

        (1) Check the code output for any issues, and return a bullet-point response addressing these points:
        * Unexpected NaN values.
        * Missing results needed for any of the tables.
        * Nominal values are reported together with measure of uncertainty (p-value, CI).
        * Imperfect implementation of statistical tests, like not accounting for confounding variables, etc.
        * Results can be understood from the output file; all values have sensible names, etc.
        * Any other issues you find.


        (2) Based on your assessment above, choose one of the following options:

        a. I didn't find any issues with the output that require correcting the code, {'choice': 'ok'}.

        b. The output does not perfectly provides everything we need for the Tables. \
        We should revise the code to better address the above issues, {'choice': 'revise'}.

        Return your choice as a Python Dict[str, str], with either: {'choice': 'ok'} or {'choice': 'revise'}.
        """)  # set to None to skip option for revision


@dataclass
class CreateTablesCodeProductsGPT(BaseScientificCodeProductsGPT):
    max_debug_iterations_per_attempt: int = 20
    max_code_revisions: int = 3
    debugger_cls: Type[DebuggerConverser] = TablesDebuggerConverser
    headers_required_in_code: Tuple[str, ...] = (
        '# IMPORT',
        '# LOAD DATA',
        '# PREPROCESSING',
        '# ANALYSIS',
        '# CREATE TABLES',
        '# OUTPUT TEXT FILE',
    )
    latex_document: LatexDocument = field(default_factory=LatexDocument)
    attrs_to_send_to_debugger: Tuple[str, ...] = \
        BaseScientificCodeProductsGPT.attrs_to_send_to_debugger + ('latex_document', 'headers_required_in_code')
    model_engine: ModelEngine = field(default_factory=lambda: get_model_engine_for_class(CreateTablesCodeProductsGPT))
    code_step: str = 'data_analysis'
    background_product_fields: Tuple[str, ...] = \
        ('data_file_descriptions', 'outputs:data_exploration', 'codes:data_preprocessing',
         'created_files_headers:data_preprocessing', 'research_goal', 'hypothesis_testing_plan')
    background_product_fields_to_hide_during_code_revision: Tuple[str, ...] = \
        ('outputs:data_exploration', 'research_goal')
    user_agent: ScientificAgent = ScientificAgent.Debugger
    allow_data_files_from_sections: Tuple[Optional[str]] = (None, 'data_exploration', 'data_preprocessing')
    supported_packages: Tuple[str, ...] = ('pandas', 'numpy', 'scipy', 'statsmodels', 'sklearn')

    output_file_requirements: OutputFileRequirements = OutputFileRequirements(
        [NumericTextContentOutputFileRequirement('results.txt'),
         TextContentOutputFileRequirement('*.tex', minimal_count=1, max_tokens=None)])
    additional_contexts: Optional[Dict[str, Any]] = field(
        default_factory=lambda: _get_additional_contexts(allow_dataframes_to_change_existing_series=True,
                                                         enforce_saving_altered_dataframes=False))
    user_initiation_prompt: str = dedent_triple_quote_str("""
        Write a complete Python code to analyze the data and create latex Tables for our scientific paper.

        The code must have the following sections (with these exact capitalized headers):

        # IMPORT
        from my_utils import to_latex_with_note, format_p_value
        <import here any other packages you need>

        As needed, you can use the following packages which are already installed:
        {supported_packages}


        # LOAD DATA
        Load the data from the original data files described above (see "{data_file_descriptions}").\
        {list_additional_data_files_if_any}


        # PREPROCESSING 
        Perform any preprocessing steps needed to prepare the data for the analysis.
        For example, as applicable:
        * Dealing with missing, unknown, or undefined values, or with special numeric values that stand for \
        unknown/undefined (check in the "{data_file_descriptions}" for any such values, and \
        consider also the "{outputs:data_exploration}").
        * Normalization of numeric values with different units into same-unit values.
        * Any other data preprocessing you deem relevant.
        * If no preprocessing is needed, write: "# No preprocessing is needed, because <your reasons here>."


        # ANALYSIS 
        Perform the analysis and appropriate statistical tests \
        (see above our "{hypothesis_testing_plan}").
        The statistical analysis should account for any relevant confounding variables, as applicable. 
        Consult with the "{hypothesis_testing_plan}" (above) for suggested tests to perform.
        Note that you may need to perform more than one test for each hypothesis.


        # CREATE TABLES
        Considering our study goals and the hypothesis testing plan (see above "{research_goal}" and \
        " "{hypothesis_testing_plan}"), create 2-4 tables for our scientific paper, summarizing \
        the results of the statistical analysis.

        For each such scientific table, create a dataframe and save it to a tex file using my custom function:
        `to_latex_with_note(df, filename: str, caption: str, label: str, \
        note: str = None, legend: Dict[str, str] = None, **kwargs)`

        This function calls pandas `df.to_latex(filename, caption=caption, label=label, **kwargs)` method, \
        and allows adding below the table an optional note (if `note` is provided) as well as an optional \
        legend mapping any abbreviated column or row names to their full names (if `legend` is provided).

        Overall, the section should have the following structure:
        ## Table 1: <your chosen table name here. e.g "Descriptive statistics of ... stratified by ...">
        <write here the code to create a dataframe of table 1 and save it using \
        `to_latex_with_note(<dataframe>, 'table_1.tex', ...)`>

        ## Table 2: <your chosen table name here. e.g "Model xxx ...">
        <write here the code to create a dateframe of table 2 and save it using \
        `to_latex_with_note(<dataframe>, 'table_2.tex', ...)`>

        etc, up to 4 tables.

        When writing the code for the Tables, consider these guidelines (as applicable):

        [a] List of tables to create:
        * Create 2-4 tables relevant to our {research_goal} and {hypothesis_testing_plan}.
        * Typically, the first table could be descriptive statistics of the data, \
        and then we should have at least one table for each of the hypothesis tests.

        [b] What to include in each table:
        * Only include information that is relevant and suitable for inclusion in a table of a scientific paper.
        * Nominal values should be accompanied by a measure of uncertainty (CI or STD).
        * Exclude data not important to the research goal, or that are too technical. \
        For example, when reporting descriptive statistics it is typically not necessary to include \
        quartile or min/max values. 
        * Make sure you do not repeat the same data in multiple tables.

        [c] P-values:
        If you are reporting P-values of statistical tests, convert them using the provided `format_p_value` func.
        This function returns: `"{:.3g}".format(x) if x >= 1e-06 else "<1e-06"`
        For example, if you have a p-value column named "p-value", then:
        `df['p-value'] = df['p-value'].apply(format_p_value)`


        # OUTPUT TEXT FILE 
        At the end of the code, after completing the tables, create an output text file named "{output_filename}", \
        and write to this file any important data that was not included in the tables.

        For example: 

        ```output                
        Total number of observations: <xxx>
        Model accuracy: <xxx>
        etc, any other global measures
        ```

        Avoid the following:
        Do not provide a sketch or pseudocode; write a complete runnable code including all '# HEADERS' sections.
        Do not create any graphics, figures or any plots.
        Do not send any presumed output examples.
        """)

    offer_revision_prompt: str = dedent_triple_quote_str("""
        I ran your code.

        {created_file_contents_explanation}

        (1) Check your Python code and return a bullet-point response addressing these points (as applicable):

        * DATASET PREPARATIONS:
        - Missing values. If applicable, did we deal with missing, unknown, or undefined values, \
        or with special numeric values that stand for unknown/undefined \
        (check the "{data_file_descriptions}" and "{outputs:data_exploration}" for any such missing values)? 
        - Units. If applicable, did we correctly standardize numeric values with different units into same-unit values? 
        - Are we restricting the analysis to the correct data (based on the study goal)?

        * DESCRIPTIVE STATISTICS:
        If applicable: 
        - did we correctly report descriptive statistics? Does the choice of variables for such \
        statistics make sense for our study?
        - Is descriptive analysis done on the correct data (for example, before any data normalization steps)?

        * PREPROCESSING:
        Review the description of the data files (see above "{data_file_descriptions}") \
        and the data exploration output (see above "{outputs:data_exploration}"), then check the code for any \
        data preprocessing steps that the code performs but are not needed, or that are needed but are not performed.

        * ANALYSIS:
        As applicable, check for any data analysis issues, including: 
        - Analysis that should be performed on the preprocessed data is mistakenly performed on the original data.
        - Incorrect choice of statistical test.
        - Imperfect implementation of statistical tests.
        - Did we correctly chose the variables that best represent the tested hypothesis? 
        {specific_comments_for_code_and_output}- Any other statistical analysis issues.

        (2) Check the created pkl tables (provided above) and \
        return a bullet-point response addressing these points:
        * Sensible numeric values: Check each numeric value in the tables and make sure it is sensible.
        For example: 
        - If the table reports the mean of a variable, is the mean value sensible?
        - If the table reports CI, are the CI values flanking the mean?
        - Do values have correct signs?
        - Do you see any values that are not sensible (too large, too small)?

        * Measures of uncertainty: If the table reports nominal values (like for regression coefs), does \
        it also report their measures of uncertainty (like p-value, CI, or STD, as applicable)?

        * Missing data in a table: Are we missing key variables in a given table?
        {comment_on_missing_table}* Any other issues you find.

        (3) Based on your assessment above, return a Python Dict[str, str] mapping the issues you have noted 
        above (dict keys) to specific suggested corrections/improvements in the code (dict values).

        For example:
        ```python
        {
            "The model does not adequately account for confounding variables": \
            "revise the code to add the following confounding variables ...",

            "A table is missing": \
            "revise the code to add the following new table '<your suggested table caption>'",

            "Table <n> reports nominal values without measures of uncertainty": \
            "revise the code to add STD and p-value.", 
        }
        ```

        Try to be as specific as possible when describing the issues and proposed fixes.
        Include in the dict as many issues as you find. 
        If you are sure that there are no issues, and the code and tables need no revision,
        then return an empty dict: `{}`. 
        """)  # set to None to skip option for revision

    def _get_specific_attrs_for_code_and_output(self, code_and_output: CodeAndOutput) -> Dict[str, str]:
        linear_regression_funcs = ['ols(', 'OLS(', 'logit(', 'Logit(', 'glm(', 'GLM(']
        comments = {}
        s = []
        code = code_and_output.code
        s.append('- Are we accounting for relevant confounding variables (consult the "{data_file_descriptions}")?')
        func_names = [func for func in linear_regression_funcs if func in code]
        if func_names:
            s.append(f'- In linear regression, if interactions terms are included:\n'
                     f'  * did we remember to include the main effects?\n'
                     f'  * did we use the `*` operator in statsmodels formula as recommended '
                     f'(as applicable, better use the `formula = "y ~ a * b"` string notation instead of trying to '
                     f'manually multiply the variables)')
        if 'mediation' in code.lower():
            s.append("- In mediation analysis:\n"
                     "  * did we calculate the mediation effect (e.g., using the Sobel test or other)?\n"
                     "  * did we account for relevant confounding factors "
                     "(by adding these same confounding factors to both the 'a' and 'b' paths)?")

        ml_funcs = ['RandomForestClassifier(', 'RandomForestRegressor(',
                    'ElasticNet(', 'SVR(', 'SVC(', 'MLPRegressor(',
                    'DecisionTreeClassifier(',
                    'DecisionTreeRegressor(', 'LogisticRegression(']
        func_names = [func for func in ml_funcs if func in code]
        if func_names:
            # func_name = func_names[0][:-1]
            s.append(
                f'- For created Machine-Learning models, check whether we adequately perform hyperparameter tuning '
                f'using cross-validation (as appropriate). Also check whether the best hyperparameters are reported '
                f'(either in the table files or in the "additional_results.pkl" file).')
        comments['specific_comments_for_code_and_output'] = '\n'.join(s) + '\n'

        num_tables = len(code_and_output.created_files.get_created_content_files_to_contents()) - 1  # -1 for result.txt
        if num_tables < 3:
            s = '* Missing tables: Considering our research goal and hypothesis testing plan, ' \
                'are all relevant tables created? If not, can you suggest any additional tables?\n'
        else:
            s = ''
        comments['comment_on_missing_table'] = s
        return comments


class PValuePickleContentOutputFileRequirement(PickleContentOutputFileRequirement):

    def get_pretty_content(self, content: Any) -> str:
        with PValue.allow_str.temporary_set(True):
            return super().get_pretty_content(content)


class DataFramePickleContentOutputFileRequirement(NumericTextContentOutputFileRequirement,
                                                  PickleContentOutputFileRequirement,
                                                  ):

    def get_pretty_content(self, content: DataFrame) -> str:
        with PValue.allow_str.temporary_set(True):
            return super().get_pretty_content(content.to_string())


class DictPickleContentOutputFileRequirement(PValuePickleContentOutputFileRequirement,
                                             NumericTextContentOutputFileRequirement):

    def get_content(self, file_path: str) -> Dict:
        result = super().get_content(file_path)
        return NiceDict(result)


@dataclass
class StatisticalTestingDebuggerConverser(DebuggerConverser):
    class_and_from_formula: Tuple[str, str] = (
        ('GLS', 'gls'),
        ('WLS', 'wls'),
        ('OLS', 'ols'),
        ('GLSAR', 'glsar'),
        ('MixedLM', 'mixedlm'),
        ('GLM', 'glm'),
        ('RLM', 'rlm'),
        ('MNLogit', 'mnlogit'),
        ('Logit', 'logit'),
        ('Probit', 'probit'),
        ('Poisson', 'poisson'),
        ('NegativeBinomial', 'negativebinomial'),
        ('QuantReg', 'quantreg'),
        ('PHReg', 'phreg'),
        ('OrdinalGEE', 'ordinal_gee'),
        ('NominalGEE', 'nominal_gee'),
        ('GEE', 'gee'),
        ('GLMGam', 'glmgam'),
        ('ConditionalLogit', 'conditional_logit'),
        ('ConditionalMNLogit', 'conditional_mnlogit'),
        ('ConditionalPoisson', 'conditional_poisson'),
    )

    def _get_issues_for_created_output_files(self, code_and_output: CodeAndOutput) -> List[RunIssue]:
        """
        Check that a PValue instance appear in at least one of the created tables.
        """
        issues = super()._get_issues_for_created_output_files(code_and_output)
        any_pvalues = False
        for file_path, content in code_and_output.created_files.get_created_content_files_to_contents().items():
            if is_containing_p_value(content):
                any_pvalues = True
                break
        if not any_pvalues:
            issues.append(RunIssue(
                issue='We are presenting results for a statistical-testing paper, but no p-values are reported in '
                      'any of the created files.',
                instructions='Please revise the code to perform statistical tests and report p-values in the tables.',
                code_problem=CodeProblem.OutputFileContentLevelA,
            ))
        return issues

    def _get_issues_for_static_code_check(self, code: str) -> List[RunIssue]:
        issues = super()._get_issues_for_static_code_check(code)

        for class_name, from_formula in self.class_and_from_formula:
            if class_name + '(' in code:
                issues.append(RunIssue(
                    issue=f'You are using the "{class_name}" class. ',
                    instructions=f'You should use the "{from_formula}" function instead, so that the '
                                 f'formula is clearly specified as a string.',
                    code_problem=CodeProblem.StaticCheck,
                ))

        return issues


@dataclass
class CreateTableDataframesCodeProductsGPT(CreateTablesCodeProductsGPT):
    debugger_cls: Type[DebuggerConverser] = StatisticalTestingDebuggerConverser
    headers_required_in_code: Tuple[str, ...] = (
        '# IMPORT',
        '# LOAD DATA',
        '# DATASET PREPARATIONS',
        '# DESCRIPTIVE STATISTICS',
        '# PREPROCESSING',
        '# ANALYSIS',
        '# SAVE ADDITIONAL RESULTS',
    )
    attrs_to_send_to_debugger: Tuple[str, ...] = \
        BaseScientificCodeProductsGPT.attrs_to_send_to_debugger + ('headers_required_in_code', )

    supported_packages: Tuple[str, ...] = ('pandas', 'numpy', 'scipy', 'statsmodels', 'sklearn', 'pickle')

    output_file_requirements: OutputFileRequirements = OutputFileRequirements(
        [DataFramePickleContentOutputFileRequirement('table_?.pkl', 2),
         DictPickleContentOutputFileRequirement('additional_results.pkl', 1),
         ])

    additional_contexts: Optional[Dict[str, Any]] = field(
        default_factory=lambda: _get_additional_contexts(allow_dataframes_to_change_existing_series=False,
                                                         enforce_saving_altered_dataframes=False,
                                                         issue_if_statistics_test_not_called=True) |
        {'ToPickleAttrReplacer': get_dataframe_to_pickle_attr_replacer(),
         'PickleDump': get_pickle_dump_attr_replacer(),
         }
    )

    user_initiation_prompt: str = dedent_triple_quote_str("""
        Write a complete Python code to analyze the data and create dataframes as basis for scientific Tables \
        for our paper.

        The code must have the following sections (with these exact capitalized headers):

        `# IMPORT`
        `import pickle`
        You can also import here any other packages you need from the following list: 
        {supported_packages}


        `# LOAD DATA`
        Load the data from the original data files described above (see "{data_file_descriptions}").\
        {list_additional_data_files_if_any}


        `# DATASET PREPARATIONS`
        * Join dataframes as needed.
        * Dealing with missing, unknown, or undefined values, or with special numeric values that stand for \
        unknown/undefined (check in the "{data_file_descriptions}" for any such values, and \
        consider also the "{outputs:data_exploration}").
        * Create new columns as needed.
        * Remove records based on exclusion/inclusion criteria (to match study goal, if applicable).
        * Standardization of numeric values with different units into same-unit values.

        If no dataset preparations are needed, write below this header: \
        `# No dataset preparations are needed.`


        `# DESCRIPTIVE STATISTICS`
        * In light of our study goals and the hypothesis testing plan (see above "{research_goal}" and \
        "{hypothesis_testing_plan}"), decide whether and which descriptive statistics are needed to be included in \
        the paper and create a relevant table.

        For example:
        `## Table 0: "Descriptive statistics of height and age stratified by sex"`
        Write here the code to create a descriptive statistics dataframe `df0` and save it using:
        `df0.to_pickle('table_0.pkl')`

        If no descriptive statistics are needed, write: \
        `# No descriptive statistics table is needed.`


        # PREPROCESSING 
        Perform any preprocessing steps needed to further prepare the data for the analysis.
        For example, as applicable:
        * Creating dummy variables for categorical variables (as needed).
        * Any other data preprocessing you deem relevant.

        If no preprocessing is needed, write:
        `# No preprocessing is needed, because <your reasons here>.`


        # ANALYSIS
        Considering our "{research_goal}" and "{hypothesis_testing_plan}", decide on 1-3 tables \
        (in addition to the above descriptive statistics, if any) we should create for our scientific paper. \
        Typically, we should have at least one table for each hypothesis test.

        For each such scientific table:
        [a] Write a comment with a suggested table's caption. 
        Choose a caption that clearly describes the table's content and its purpose.
        For example:
        `## Table 1: "Test of association between age and risk of death, accounting for sex and race"`
        Avoid generic captions such as `## Table 1: "Results of analysis"`.

        [b] Perform analysis
        - Perform appropriate analysis and/or statistical tests (see above our "{hypothesis_testing_plan}").
        - The statistical analysis should account for any relevant confounding variables, as applicable.
        - Note that you may need to perform more than one test for each hypothesis.
        - Try using inherent functionality and syntax provided in functions from the available \
        Python packages (above) and avoid, as possible, manually implementing generically available functionality.
        For example, to include interactions in regression analysis (if applicable), use the "x * y" string syntax \
        in statsmodels formulas.{mediation_note_if_applicable}

        [c] Create and save a dataframe for a scientific table
        * Create a dataframe containing the data needed for the table (`df1`, `df2`, etc). 
        * Only include information that is relevant and suitable for inclusion in a scientific table.
        * Nominal values should be accompanied by a measure of uncertainty (CI or STD and p-value).
        * Exclude data not important to the research goal, or that are too technical.
        * Make sure you do not repeat the same data in multiple tables.
        * The table should have labels for the both the columns and the index (rows): 
            - Do not invent new names; just keep the original variable names from the dataset.
            - As applicable, also keep unmodified any attr names from statistical test results.


        Overall, the section should have the following structure:

        # ANALYSIS
        ## Table 1: <your chosen table name here>
        <write here the code to analyze the data and create a dataframe df1 for the table 1>
        df1.to_pickle('table_1.pkl')

        ## Table 2: <your chosen table name here>
        etc, up to 3 tables.


        # SAVE ADDITIONAL RESULTS
        At the end of the code, after completing the tables, create a dict containing any additional \
        results you deem important to include in the scientific paper, and save it to a pkl file \
        'additional_results.pkl'. 

        For example:

        `additional_results = {
            'Total number of observations': <xxx>,         
            'accuracy of regression model': <xxx>,
            # etc, any other results and important parameters that are not included in the tables
        }
        with open('additional_results.pkl', 'wb') as f:
            pickle.dump(additional_results, f)
        `

        Avoid the following:
        Do not provide a sketch or pseudocode; write a complete runnable code including all '# HEADERS' sections.
        Do not create any graphics, figures or any plots.
        Do not send any presumed output examples.
        Avoid convoluted or indirect methods of data extraction and manipulation; \
        Where possible, use direct attribute access for clarity and simplicity.
        Where possible, access dataframes using string-based column/index names, \
        rather than integer-based column/index positions. 
        """)

    @property
    def mediation_note_if_applicable(self):
        keywords = ['mediated', 'mediation', 'mediates', 'mediator', 'mediators']
        for hypothesis, plan in self.products.hypothesis_testing_plan.items():
            if any(keyword in hypothesis.lower() or keyword in plan.lower() for keyword in keywords):
                return f"\n" \
                       f"- If you are doing a mediation analysis, don't forget to calculate both the 'a' and 'b' " \
                       f"paths (and add the same confounding variables to both paths, as needed)."
        return ''


@dataclass
class DataframePreventAssignmentToAttrs(PreventAssignmentToAttrs):
    obj_import_str: str = 'pandas.DataFrame'
    forbidden_set_attrs: Tuple[str, ...] = ('columns', 'index')

    def _raise_exception(self, attr, value):
        raise RunUtilsError(RunIssue(
            issue=f"To avoid mistakes, please do not directly assign to '{attr}'.",
            code_problem=CodeProblem.NonBreakingRuntimeIssue,
            instructions=f'Use instead `df.rename({attr}=<mapping>, inplace=True)`',
        ))


@dataclass
class CreateLatexTablesCodeProductsGPT(CreateTablesCodeProductsGPT):
    code_step: str = 'data_to_latex'
    headers_required_in_code: Tuple[str, ...] = ('# IMPORT', '# PREPARATION FOR ALL TABLES')
    phrases_required_in_code: Tuple[str, ...] = \
        ('\nfrom my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping', )
    attrs_to_send_to_debugger: Tuple[str, ...] = \
        CreateTablesCodeProductsGPT.attrs_to_send_to_debugger + ('phrases_required_in_code', )

    background_product_fields: Tuple[str, ...] = \
        ('data_file_descriptions', 'research_goal', 'codes:data_preprocessing', 'codes:data_analysis',
         'created_files_content:data_analysis:table_?.pkl')
    background_product_fields_to_hide_during_code_revision: Tuple[str, ...] = \
        ('research_goal', 'codes:data_preprocessing', 'created_files_content:data_analysis:*.pkl')
    allow_data_files_from_sections: Tuple[Optional[str]] = ('data_analysis', )
    supported_packages: Tuple[str, ...] = ('pandas', 'numpy', 'my_utils')
    additional_contexts: Optional[Dict[str, Any]] = field(
        default_factory=lambda: _get_additional_contexts(
            allow_dataframes_to_change_existing_series=True,
            enforce_saving_altered_dataframes=False) |
        {'CustomPreventMethods': PreventCalling(
            modules_and_functions=(
                ('pandas.DataFrame', 'to_latex', False),
                ('pandas.DataFrame', 'to_html', False),
                ('pandas', 'to_numeric', False),
            )
        ),
         'CustomPreventAssignmentToAtt': DataframePreventAssignmentToAttrs(
            forbidden_set_attrs=['columns', 'index'],
        ),
         'PValueMessage': AttrReplacer(
             obj_import_str=PValue, attr='error_message_on_forbidden_func',
             wrapper="Calling `{func_name}` on a PValue object is forbidden.\n Please use `format_p_value` instead."
        )}
    )

    output_file_requirements: OutputFileRequirements = OutputFileRequirements(
        [TextContentOutputFileRequirement('*.tex', minimal_count=1, max_tokens=None)])

    provided_code: str = dedent_triple_quote_str('''
        def to_latex_with_note(df, filename: str, caption: str, label: str, \
        note: str = None, legend: Dict[str, str] = None, **kwargs):
            """
            Converts a DataFrame to a LaTeX table with optional note and legend added below the table.

            Parameters:
            - df, filename, caption, label: as in `df.to_latex`.
            - note (optional): Additional note below the table.
            - legend (optional): Dictionary mapping abbreviations to full names.
            - **kwargs: Additional arguments for `df.to_latex`.

            Returns:
            - None: Outputs LaTeX file.
            """

        def format_p_value(x):
            returns "{:.3g}".format(x) if x >= 1e-06 else "<1e-06"

        def is_str_in_df(df: pd.DataFrame, s: str):
            return any(s in level for level in getattr(df.index, 'levels', [df.index]) + \
        getattr(df.columns, 'levels', [df.columns]))

        AbbrToNameDef = Dict[Any, Tuple[Optional[str], Optional[str]]]

        def split_mapping(abbrs_to_names_and_definitions: AbbrToNameDef):
            abbrs_to_names = {abbr: name for abbr, (name, definition) in \
        abbrs_to_names_and_definitions.items() if name is not None}
            names_to_definitions = {name or abbr: definition for abbr, (name, definition) in \
        abbrs_to_names_and_definitions.items() if definition is not None}
            return abbrs_to_names, names_to_definitions
        ''')

    user_initiation_prompt: str = dedent_triple_quote_str('''
        I would like to create latex tables for our scientific paper from the dataframes created \
        in the code above ("table_?.pkl" files). 

        I would like to convert these dataframes to latex tables, using the following 4 custom functions that I wrote: 

        ```python
        {provided_code}
        ```

        Please write a complete Python code that uses the above functions to convert our dataframes \
        to latex tables suitable for our scientific paper. Follow these instructions:

        Rename column and row names: You should provide a new name to any column or row label that is abbreviated \
        or technical, or that is otherwise not self-explanatory.

        Full definitions: You should provide an optional full definition for any name (or new name) \
        that satisfies any of the following: 
        - Remains abbreviated, or not self-explanatory, even after renaming
        - Is an ordinal/categorical value that requires clarification of the meaning of each value.
        - Contains possibly unclear notation, like '*' or ':'
        - Is a numeric value that has units, that need to be specified.        

        To avoid re-naming mistakes, I strongly suggest you define for each table a dictionary, \
        `mapping: AbbrToNameDef`, which maps any original \
        column and row labels that are abbreviated or not self-explanatory to an optional new name, \
        and an optional definition.
        If different tables share several common labels, then you can build these table-specific mappings \
        from a `shared_mapping`. See example below.

        Overall, the code must have the following structure:

        ```
        # IMPORT
        import pandas as pd
        from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

        # PREPARATION FOR ALL TABLES

        < As applicable, define a shared mapping for labels that are common to all tables. For example: >

        shared_mapping: AbbrToNameDef = {
            'AvgAge': ('Avg. Age', 'Average age, years'),
            'BT': ('Body Temperature', '1: Normal, 2: High, 3: Very High'),
            'W': ('Weight', 'Participant weight, kg'),
            'MRSA': (None, 'Infected with Methicillin-resistant Staphylococcus aureus, 1: Yes, 0: No'),
            ...: (..., ...),
        }
        < This is of course just an example. Consult with the "{data_file_descriptions}" \
        and the "{codes:data_analysis}" for choosing the common labels and their appropriate scientific names \
        and definitions. >

        # TABLE {first_table_number}:
        df = pd.read_pickle('table_{first_table_number}.pkl')

        # FORMAT VALUES <include this sub-section only as applicable>
        < Rename technical values to scientifically-suitable values. For example: >
        df['MRSA'] = df['MRSA'].apply(lambda x: 'Yes' if x == 1 else 'No')

        < If the table has P-values from statistical tests, format them with `format_p_value`. For example: >
        df['PV'] = df['PV'].apply(format_p_value)

        # RENAME ROWS AND COLUMNS <include this sub-section only as applicable>
        < Rename any abbreviated or not self-explanatory table labels to scientifically-suitable names. >
        < Use the `shared_mapping` if applicable. For example: >
        mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)} 
        mapping |= {
            'PV': ('P-value', None),
            'CI': (None, '95% Confidence Interval'),
            'Sex_Age': ('Age * Sex', 'Interaction term between Age and Sex'),
        }
        abbrs_to_names, legend = split_mapping(mapping)
        df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

        # Save as latex:
        to_latex_with_note(
            df, 'table_1.tex',
            caption="<choose a caption suitable for a table in a scientific paper>", 
            label='table:<chosen table label>',
            note="<If needed, add a note to provide any additional information that is not captured in the caption>",
            legend=legend)


        # TABLE <?>:
        < etc, all 'table_?.pkl' files >
        ```

        Avoid the following:
        Do not provide a sketch or pseudocode; write a complete runnable code including all '# HEADERS' sections.
        Do not create any graphics, figures or any plots.
        Do not send any presumed output examples.
        ''')

    offer_revision_prompt: str = None

    @property
    def first_table_number(self):
        k = len('table_')
        return self.products.get_created_df_tables()[0][k]

    def __post_init__(self):
        super().__post_init__()
        k = len('table_')
        self.headers_required_in_code += tuple(f'# TABLE {file_name[k]}'
                                               for file_name in self.products.get_created_df_tables())


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
        return self.code_and_output.created_files.get_single_content_file()


@dataclass
class RequestCodeExplanation(BaseScientificPostCodeProductsHandler, LatexReviewBackgroundProductsConverser):
    goal_noun: str = 'explanation of the {code_name} code'
    background_product_fields: Tuple[str, ...] = ('data_file_descriptions',)
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
        Focus on analysis steps. There is no need to explain trivial parts, like reading/writing a file, etc.  
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
        return self.requesting_output_explanation \
            if self.code_and_output.created_files.get_single_content_file() else ''

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
        with open(f'{self.output_directory}/{code_step}.py', 'w') as f:
            f.write(code_and_output.code)

    def get_code_and_output(self) -> CodeAndOutput:
        code_writing = self.code_writing_class.from_(self)
        assert code_writing.code_step == self.code_step
        return code_writing.get_code_and_output()

    def _get_description_of_created_files(self) -> Optional[DataFileDescriptions]:
        return self.explain_created_files_class.from_(
            self,
            is_new_conversation=None,
            code_step=self.code_step,
        ).ask_for_created_files_descriptions()

    def _get_code_explanation(self) -> str:
        return self.explain_code_class.from_(
            self,
            is_new_conversation=None,
            code_step=self.code_step,
        ).run_dialog_and_get_valid_result()

    def get_code_and_output_and_descriptions(self) -> CodeAndOutput:
        code_and_output = self.get_code_and_output()
        self.products.codes_and_outputs[self.code_step] = code_and_output
        if self.explain_code_class:
            code_and_output.code_explanation = self._get_code_explanation()
        if self.explain_created_files_class and code_and_output.created_files.get_created_data_files():
            code_and_output.description_of_created_files = self._get_description_of_created_files()
        self._save_code_to_file(self.code_step, code_and_output)
        return code_and_output
