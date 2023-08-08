from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Tuple, Dict, Type, List

from data_to_paper.base_products import DataFileDescription, DataFileDescriptions
from data_to_paper.base_steps import BaseCodeProductsGPT, PythonDictWithDefinedKeysReviewBackgroundProductsConverser, \
    BackgroundProductsConverser, LatexReviewBackgroundProductsConverser
from data_to_paper.base_steps.base_products_conversers import ProductsConverser, ReviewBackgroundProductsConverser
from data_to_paper.base_steps.debugger import DebuggerConverser
from data_to_paper.base_steps.result_converser import Rewind
from data_to_paper.conversation.actions_and_conversations import ActionsAndConversations
from data_to_paper.latex import extract_latex_section_from_response
from data_to_paper.latex.latex_doc import LatexDocument

from data_to_paper.researches_types.scientific_research.cast import ScientificAgent
from data_to_paper.researches_types.scientific_research.scientific_products import ScientificProducts, get_code_name, \
    get_code_agent
from data_to_paper.researches_types.scientific_research.table_debugger import TablesDebuggerConverser

from data_to_paper.run_gpt_code.types import CodeAndOutput, OutputFileRequirement, ContentOutputFileRequirement, \
    DataOutputFileRequirement, RunIssue, CodeProblem, NumericContentOutputFileRequirement
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
                files += self.products.codes_and_outputs[section].get_created_data_files()
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


@dataclass
class DataExplorationDebugger(DebuggerConverser):
    headers_required_in_output: Tuple[str, ...] = \
        ('# Data Size', '# Summary Statistics', '# Categorical Variables', '# Missing Values')

    def _get_issues_for_output_file_content(self, requirement: ContentOutputFileRequirement,
                                            filename: str, content: str) -> List[RunIssue]:
        issues = super()._get_issues_for_output_file_content(requirement, filename, content)
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
    debugger_cls: DebuggerConverser = DataExplorationDebugger

    code_step: str = 'data_exploration'
    background_product_fields: Tuple[str, ...] = ('all_file_descriptions', )
    user_agent: ScientificAgent = ScientificAgent.DataExplorer
    allow_data_files_from_sections: Tuple[Optional[str]] = (None, )

    output_file_requirements: Tuple[OutputFileRequirement, ...] = \
        (ContentOutputFileRequirement('data_exploration.txt'), )
    allowed_created_files: Tuple[str, ...] = ()
    allow_dataframes_to_change_existing_series = False
    enforce_saving_altered_dataframes: bool = False

    supported_packages: Tuple[str, ...] = ('pandas', 'numpy', 'scipy')

    user_initiation_prompt: str = dedent_triple_quote_str("""
        As part of a data-exploration phase, please write a complete short Python code for getting a \
        first sense of the data. 

        Your code should create an output text file named "{output_filename}", which should \
        contain a summary of the data.

        The output file should be self-contained; any results you choose to save to this file \
        should be accompanied with a header or a short label and indication of units (if any).

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
        * Do all numeric values have units (if applicable).
        * Are there any results that are missing. Check that under each header in the output file there is \
        a corresponding meaningful result.
        * Any other issues you find.

        (2) Based on your assessment above, return a Python Dict[str, str] mapping the issues you have noted \
        above (dict keys) to specific suggested corrections/improvements in the code (dict values).
        
        For example:
        ```python
        {
            "The result of the average of variable ... is missing": \
            "Add the missing calculation of to the code.",
            "The average of the variable ... is printed without units": \
            "Based on the data description, the units should be ...",
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

    output_file_requirements: Tuple[OutputFileRequirement, ...] = (DataOutputFileRequirement('*.csv'), )
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

    output_file_requirements: Tuple[OutputFileRequirement, ...] = (ContentOutputFileRequirement('results.txt'), )
    allow_dataframes_to_change_existing_series: bool = True
    enforce_saving_altered_dataframes: bool = False
    model_engine: ModelEngine = ModelEngine.GPT4

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
    latex_document: LatexDocument = field(default_factory=LatexDocument)
    attrs_to_send_to_debugger: Tuple[str, ...] = \
        BaseScientificCodeProductsGPT.attrs_to_send_to_debugger + ('latex_document', )

    code_step: str = 'data_analysis'
    background_product_fields: Tuple[str, ...] = \
        ('data_file_descriptions', 'outputs:data_exploration', 'codes:data_preprocessing',
         'created_files_headers:data_preprocessing', 'research_goal', 'hypothesis_testing_plan')
    background_product_fields_to_hide_during_code_revision: Tuple[str, ...] = \
        ('outputs:data_exploration', 'research_goal')
    user_agent: ScientificAgent = ScientificAgent.Debugger
    allow_data_files_from_sections: Tuple[Optional[str]] = (None, 'data_exploration', 'data_preprocessing')
    supported_packages: Tuple[str, ...] = ('pandas', 'numpy', 'scipy', 'statsmodels', 'sklearn')

    output_file_requirements: Tuple[OutputFileRequirement, ...] = \
        (ContentOutputFileRequirement('results.txt'), ContentOutputFileRequirement('*.tex', minimal_count=1))
    allow_dataframes_to_change_existing_series: bool = True
    enforce_saving_altered_dataframes: bool = False
    model_engine: ModelEngine = ModelEngine.GPT4

    user_initiation_prompt: str = dedent_triple_quote_str("""
        Write a complete Python code to analyze the data and create latex Tables for our scientific paper.

        The code must have the following sections (with these exact capitalized headers):

        # IMPORT
        from my_utils import to_latex_with_note
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


        # CREATE TABLES
        Considering the our study goals and the hypothesis testing plan (see above "{research_goal}" and \
        " "{hypothesis_testing_plan}"), create 2-4 tables for our scientific paper, summarizing \
        the results of the statistical analysis.
        
        For each such scientific table, create a dataframe and save it to a tex file using my custom function:
        `to_latex_with_note(df, filename: str, *args, \
        caption=str, note: str = None, legend: Dict[str, str] = None, **kwargs)`

        This function calls pandas `df.to_latex(filename, *args, caption=caption, **kwargs)` method, \
        then adds at the end of the table a text note (if `note` is provided) as well as a legend which maps \
        any abbreviated column or row names to their full names (if `legend` is provided).

        Overall, the section should have the following structure:
        ## Table 1: <your chosen table name here. e.g "Descriptive statistics of ...">
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
        * Nominal values should be accompanied by a measure of uncertainty (p-value, CI, STD, etc).
        * Exclude data not important to the research goal, or that are too technical. \
        For example, when reporting descriptive statistics it is typically not necessary to include \
        quartile or min/max values. 
        * Make sure you do not repeat the same data in multiple tables.

        [c] P-values:
        If P-values are included, convert them using:
        `p_value_replacer = lambda x: "{:.3g}".format(x) if x >= 1e-4 else "<1e-4"`
        For example, if you have a p-value column named "p-value", then:
        `df['p-value'] = df['p-value'].apply(p_value_replacer)`

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

        (1) Check your Python code and return a bullet-point response addressing these points:
        
        * Statistical analysis: Check the part of the code that performs the statistical analysis, \
        and identify any imperfect implementation of statistical tests, like:
        - Incorrect choice of statistical test.
        {specific_comments_for_code_and_output}- Any other statistical analysis issues.
        
        * Preprocessing: Review the description of the data files (see above "{data_file_descriptions}") \
        and the data exploration output (see above "{outputs:data_exploration}"), then check the code for any \
        data preprocessing steps that the code performs but are not needed, or that are needed but are not performed.
        
        * Data Analysis: Check for any data analysis issues. For example, analysis that should be performed on the \
        raw data is performed on the preprocessed data, or vice versa.

        (2) Check the created tables (latex code blocks above) and \
        return a bullet-point response addressing these points:
        * Measures of uncertainty: If the table reports nominal values (like for regression coefs), does \
        it also report their measures of uncertainty (like p-value, CI, or STD, as applicable)?
        * Missing data in a table: Are we missing key variables in a given table?
        {comment_on_missing_table}* P-values: If p-values are presented, \
        are all lower than 1e-4 p-values correctly converted to "<1e-4". \
        Check also that this conversion is correctly applied to the right variables (the P-value variables).
        * Any other issues you find.

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
        then return an empty dict: {}. 
        """)  # set to None to skip option for revision

    def _get_specific_attrs_for_code_and_output(self, code_and_output: CodeAndOutput) -> Dict[str, str]:
        comments = {}
        s = []
        code = code_and_output.code
        s.append('- Are we accounting for relevant confounding variables (consult the "{data_file_descriptions}")?')
        if 'ols(' in code or 'OLS(' in code:
            s.append('- In linear regression, if interactions terms are included, '
                     'did we remember to include the main effects?')

        comments['specific_comments_for_code_and_output'] = '\n'.join(s) + '\n'

        num_tables = len(code_and_output.get_created_content_files_to_contents()) - 1  # -1 for result.txt
        if num_tables < 3:
            s = '* Missing tables: Considering our research goal and hypothesis testing plan, ' \
                'are all relevant tables created? If not, can you suggest any additional tables?\n'
        else:
            s = ''
        comments['comment_on_missing_table'] = s
        return comments

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
        return self.code_and_output.get_single_output_filename()


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
        return self.requesting_output_explanation if self.code_and_output.get_single_output_filename() else ''

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
    'data_analysis': CreateTablesCodeProductsGPT,
}


@dataclass
class RequestCodeProducts(BaseScientificCodeProductsHandler, ProductsConverser):
    EXPLAIN_CODE_CLASS = RequestCodeExplanation
    EXPLAIN_CREATED_FILES_CLASS = ExplainCreatedDataframe
    latex_document: LatexDocument = None

    @property
    def code_writing_class(self) -> Type[BaseScientificCodeProductsGPT]:
        return CODE_STEP_TO_CLASS[self.code_step]

    def get_code_writing_instance(self) -> BaseScientificCodeProductsGPT:
        cls = self.code_writing_class
        if self.code_step == 'data_analysis':
            num_tables = 2
            return cls.from_(
                self,
                latex_document=self.latex_document,
                output_file_requirements=(NumericContentOutputFileRequirement('results.txt'),
                                          ContentOutputFileRequirement('table_?.tex', num_tables)),
            )
        return cls.from_(self)

    def get_code_and_output(self) -> CodeAndOutput:
        return self.get_code_writing_instance().get_code_and_output()

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
        if with_file_descriptions and code_and_output.get_created_data_files():
            code_and_output.description_of_created_files = self._get_description_of_created_files()
        return code_and_output
