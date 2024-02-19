from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Tuple, Dict, Type, List, Any, Iterable

from data_to_paper.base_products import DataFileDescription, DataFileDescriptions
from data_to_paper.base_steps import BaseCodeProductsGPT, PythonDictWithDefinedKeysReviewBackgroundProductsConverser, \
    BackgroundProductsConverser, LatexReviewBackgroundProductsConverser
from data_to_paper.base_steps.base_products_conversers import ProductsConverser, ReviewBackgroundProductsConverser
from data_to_paper.base_steps.debugger import DebuggerConverser
from data_to_paper.base_steps.result_converser import Rewind
from data_to_paper.code_and_output_files.file_view_params import ContentViewPurpose, ContentViewParams, ContentView
from data_to_paper.code_and_output_files.ref_numeric_values import HypertargetFormat, HypertargetPosition
from data_to_paper.code_and_output_files.referencable_text import BaseReferenceableText, convert_str_to_latex_label
from data_to_paper.conversation.actions_and_conversations import ActionsAndConversations
from data_to_paper.latex import extract_latex_section_from_response
from data_to_paper.latex.latex_doc import LatexDocument
from data_to_paper.latex.tables import get_table_caption

from data_to_paper.research_types.scientific_research.cast import ScientificAgent
from data_to_paper.research_types.scientific_research.scientific_products import ScientificProducts, get_code_name, \
    get_code_agent, HypertargetPrefix
from data_to_paper.research_types.scientific_research.table_debugger import TablesDebuggerConverser
from data_to_paper.research_types.scientific_research.utils_for_gpt_code.utils_modified_for_gpt_use.to_latex_with_note \
    import TABLE_COMMENT_HEADER
from data_to_paper.run_gpt_code.overrides.attr_replacers import PreventAssignmentToAttrs, PreventCalling, AttrReplacer
from data_to_paper.run_gpt_code.overrides.contexts import OverrideStatisticsPackages
from data_to_paper.run_gpt_code.overrides.dataframes import TrackDataFrames
from data_to_paper.run_gpt_code.overrides.dataframes.df_methods.methods import temporarily_change_float_format, \
    STR_FLOAT_FORMAT
from data_to_paper.run_gpt_code.overrides.pvalue import PValue, is_containing_p_value, OnStr

from data_to_paper.code_and_output_files.code_and_output import CodeAndOutput
from data_to_paper.run_gpt_code.overrides.scipy.override_scipy import ScipyPValueOverride
from data_to_paper.run_gpt_code.run_issues import CodeProblem, RunIssue
from data_to_paper.code_and_output_files.output_file_requirements import DataOutputFileRequirement, \
    PickleContentOutputFileRequirement, TextContentOutputFileRequirement, NumericTextContentOutputFileRequirement, \
    OutputFileRequirements
from data_to_paper.servers.model_engine import ModelEngine
from data_to_paper.research_types.scientific_research.model_engines import get_model_engine_for_class
from data_to_paper.utils import dedent_triple_quote_str
from data_to_paper.utils.nice_list import NiceList, NiceDict
from data_to_paper.utils.replacer import Replacer
from data_to_paper.utils.types import ListBasedSet
from data_to_paper.research_types.scientific_research.utils_for_gpt_code.utils_modified_for_gpt_use.to_pickle import \
    get_dataframe_to_pickle_attr_replacer, get_pickle_dump_attr_replacer, get_read_pickle_attr_replacer


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
    background_product_fields: Tuple[str, ...] = ('all_file_descriptions', 'research_goal')
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
                category='Output file content',
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
    additional_contexts: Optional[Dict[str, Any]] = field(
        default_factory=lambda: _get_additional_contexts(allow_dataframes_to_change_existing_series=False,
                                                         enforce_saving_altered_dataframes=False))

    supported_packages: Tuple[str, ...] = ('pandas', 'numpy', 'scipy')

    user_initiation_prompt: str = dedent_triple_quote_str("""
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

        If any of the above sections is not applicable, then write "Not Applicable" under that section.

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
            "The average of the variable <xxx> is `Nan`": \t
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


@dataclass
class DataPreprocessingCodeProductsGPT(BaseScientificCodeProductsGPT):
    code_step: str = 'data_preprocessing'
    background_product_fields: Tuple[str, ...] = ('research_goal', 'all_file_descriptions', 'outputs:data_exploration')
    # user_agent: ScientificAgent = ScientificAgent.DataPreprocessor
    allow_data_files_from_sections: Tuple[Optional[str]] = (None, 'data_exploration', )
    supported_packages: Tuple[str, ...] = ('pandas', 'numpy', 'scipy', 'imblearn')

    output_file_requirements: OutputFileRequirements = OutputFileRequirements([DataOutputFileRequirement('*.csv')])
    additional_contexts: Optional[Dict[str, Any]] = field(
        default_factory=lambda: _get_additional_contexts(allow_dataframes_to_change_existing_series=False,
                                                         enforce_saving_altered_dataframes=True))

    user_initiation_prompt: str = dedent_triple_quote_str("""
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


@dataclass
class BaseCreateTablesCodeProductsGPT(BaseScientificCodeProductsGPT):
    max_debug_iterations_per_attempt: int = 20
    max_code_revisions: int = 3
    headers_required_in_code: Tuple[str, ...] = ()
    attrs_to_send_to_debugger: Tuple[str, ...] = \
        BaseScientificCodeProductsGPT.attrs_to_send_to_debugger + ('headers_required_in_code', )
    model_engine: ModelEngine = \
        field(default_factory=lambda: get_model_engine_for_class(BaseCreateTablesCodeProductsGPT))
    user_agent: ScientificAgent = ScientificAgent.Debugger
    supported_packages: Tuple[str, ...] = ('pandas', 'numpy', 'scipy', 'statsmodels', 'sklearn')

    @staticmethod
    def _get_regression_comments_for_code_and_output(code_and_output: CodeAndOutput) -> str:
        if 'statsmodels' not in code_and_output.code:
            return ''
        linear_regression_funcs = ['ols(', 'OLS(', 'logit(', 'Logit(', 'glm(', 'GLM(']
        code = code_and_output.code
        func_names = [func for func in linear_regression_funcs if func in code]
        if not func_names:
            return ''
        return dedent_triple_quote_str("""
            - In linear regression, if interactions terms are included:
              * did we remember to include the main effects?
              * did we use the `*` operator in statsmodels formula as recommended? \t
            (as applicable, better use `formula = "y ~ a * b"`, instead of trying to \t
            manually multiply the variables)
            """)

    @staticmethod
    def _get_mediation_comments_for_code_and_output(code_and_output: CodeAndOutput) -> str:
        if 'mediation' not in code_and_output.code.lower():
            return ''
        return dedent_triple_quote_str("""
            - In mediation analysis:
              * did we calculate the mediation effect (e.g., using the Sobel test or other)?
              * did we account for relevant confounding factors? \t
            (by adding these same confounding factors to both the 'a' and 'b' paths)
            """)

    @staticmethod
    def _get_machine_learning_comments_for_code_and_output(code_and_output: CodeAndOutput) -> str:
        if 'sklearn' not in code_and_output.code:
            return ''
        ml_funcs = ['RandomForestClassifier(', 'RandomForestRegressor(',
                    'ElasticNet(', 'SVR(', 'SVC(', 'MLPRegressor(',
                    'DecisionTreeClassifier(',
                    'DecisionTreeRegressor(', 'LogisticRegression(']
        func_names = [func for func in ml_funcs if func in code_and_output.code]
        if not func_names:
            return ''
        return dedent_triple_quote_str("""
            - For created Machine-Learning models:
              * Check whether we adequately perform hyperparameter tuning using cross-validation (as appropriate). 
              * Check whether the best hyperparameters are reported \t
              (either in a table file or in the "additional_results.pkl" file).
            """)

    @staticmethod
    def _get_scipy_unpacking_comments_for_code_and_output(code_and_output: CodeAndOutput) -> str:
        override_stats = code_and_output.contexts['OverrideStatisticsPackages']
        assert isinstance(override_stats, OverrideStatisticsPackages)
        stat_contexts = override_stats.contexts
        scipy_context = next((context for context in stat_contexts if isinstance(context, ScipyPValueOverride)), None)
        if scipy_context:
            func_to_fields = scipy_context.unpacking_func_to_fields
            if func_to_fields:
                s = '- When unpacking or indexing the results of {}, are we using the correct order of fields?\n'. \
                    format(NiceList(func_to_fields.keys(), wrap_with="`", last_separator=" or "))
                for func, fields in func_to_fields.items():
                    s += f'  The correct order for `{func}` is: {NiceList(fields, wrap_with="`")}.\n'
                return s
        return ''

    def _get_specific_attrs_for_code_and_output(self, code_and_output: CodeAndOutput) -> Dict[str, str]:
        comments = super()._get_specific_attrs_for_code_and_output(code_and_output)
        comments['regression_comments'] = self._get_regression_comments_for_code_and_output(code_and_output)
        comments['mediation_comments'] = self._get_mediation_comments_for_code_and_output(code_and_output)
        comments['machine_learning_comments'] = self._get_machine_learning_comments_for_code_and_output(code_and_output)
        comments['scipy_unpacking_comments'] = self._get_scipy_unpacking_comments_for_code_and_output(code_and_output)
        return comments


class DataFramePickleContentOutputFileRequirement(PickleContentOutputFileRequirement):

    def _to_str(self, content: Any) -> str:
        with temporarily_change_float_format(STR_FLOAT_FORMAT):
            return content.to_string()


class DictPickleContentOutputFileRequirement(PickleContentOutputFileRequirement,
                                             NumericTextContentOutputFileRequirement):

    def get_content(self, file_path: str) -> Dict:
        result = super().get_content(file_path)
        return NiceDict(result)


@dataclass
class DataAnalysisCodeAndOutput(CodeAndOutput):
    def _get_code_header_for_file(self, filename: str) -> str:
        # 'table_?.pkl' -> '# Table ?'
        if filename.startswith('table_') and filename.endswith('.pkl'):
            return f'# Table {filename[6:-4]}'
        # 'additional_results.pkl' -> '# Additional Results'
        if filename == 'additional_results.pkl':
            return '# SAVE ADDITIONAL RESULTS'
        return super()._get_code_header_for_file(filename)


@dataclass
class CreateLatexTablesCodeAndOutput(CodeAndOutput):
    def _get_code_header_for_file(self, filename: str) -> str:
        # 'table_?.tex' -> '# TABLE ?'
        if filename.startswith('table_') and filename.endswith('.tex'):
            return f'# TABLE {filename[6:-4]}'
        return super()._get_code_header_for_file(filename)


@dataclass
class DataAnalysisDebuggerConverser(DebuggerConverser):
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

    def _get_issues_for_created_output_files(self, code_and_output: CodeAndOutput, contexts) -> List[RunIssue]:
        """
        Check that a PValue instance appear in at least one of the created tables.
        """
        issues = super()._get_issues_for_created_output_files(code_and_output, contexts)
        any_pvalues = False
        for names_to_contents in code_and_output.created_files.values():
            for content in names_to_contents.values():
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
        if issues:
            return issues
        return self._get_issues_for_table_comments(code_and_output, contexts)

    def _get_issues_for_table_comments(self, code_and_output: CodeAndOutput, contexts) -> List[RunIssue]:
        context = contexts['ToPickleAttrReplacer']
        prior_tables = getattr(context, 'prior_tables', {})
        code = code_and_output.code
        issues = []
        for table_file_name in prior_tables.keys():
            table_name = table_file_name.split('.')[0].replace('_', ' ').title()
            if f'## {table_name}' not in code:
                issues.append(RunIssue(
                    category="Each saved table should have a header comment with the table name.\n",
                    issue=f'Your code is missing a comment "## {table_name}".',
                    instructions='Please make sure all saved tables have a header comment with the table name.\n'
                                 'If you are creating multiple tables in the same section of the code, '
                                 'you should precede this section with a separate comment for each of the tables.',
                    code_problem=CodeProblem.OutputFileContentLevelA,
                ))
        return issues

    def _get_issues_for_static_code_check(self, code: str) -> List[RunIssue]:
        issues = super()._get_issues_for_static_code_check(code)

        for class_name, from_formula in self.class_and_from_formula:
            if class_name + '(' in code:
                issues.append(RunIssue(
                    issue=f'You are using the "{class_name}" class. ',
                    instructions=dedent_triple_quote_str(f"""
                        You should use the "{from_formula}" function instead, so that the formula is clearly \t
                        specified as a string. 
                        Reminder: For interactions, if any, use the `*` operator in the formula, rather than \t
                        manually multiplying the variables.
                        """),
                    code_problem=CodeProblem.StaticCheck,
                ))

        return issues


@dataclass
class DataAnalysisCodeProductsGPT(BaseCreateTablesCodeProductsGPT):
    code_step: str = 'data_analysis'
    debugger_cls: Type[DebuggerConverser] = DataAnalysisDebuggerConverser
    code_and_output_cls: Type[CodeAndOutput] = DataAnalysisCodeAndOutput
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

    background_product_fields: Tuple[str, ...] = \
        ('data_file_descriptions', 'outputs:data_exploration', 'codes:data_preprocessing',
         'created_files_headers:data_preprocessing', 'research_goal', 'hypothesis_testing_plan')
    background_product_fields_to_hide_during_code_revision: Tuple[str, ...] = \
        ('outputs:data_exploration', 'research_goal')
    allow_data_files_from_sections: Tuple[Optional[str]] = (None, 'data_exploration', 'data_preprocessing')

    supported_packages: Tuple[str, ...] = ('pandas', 'numpy', 'scipy', 'statsmodels', 'sklearn', 'pickle')

    output_file_requirements: OutputFileRequirements = OutputFileRequirements(
        [DataFramePickleContentOutputFileRequirement('table_?.pkl', 1),
         DictPickleContentOutputFileRequirement('additional_results.pkl', 1,
                                                hypertarget_prefixes=HypertargetPrefix.ADDITIONAL_RESULTS.value)
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
        Write a complete Python code to analyze the data and create dataframes as basis for scientific Tables \t
        for our paper.

        The code must have the following sections (with these exact capitalized headers):

        `# IMPORT`
        `import pickle`
        You can also import here any other packages you need from: 
        {supported_packages}


        `# LOAD DATA`
        Load the data from the original data files described above (see "{data_file_descriptions}").
        {list_additional_data_files_if_any}\t


        `# DATASET PREPARATIONS`
        * Join data files as needed.
        * Dealing with missing, unknown, or undefined values, or with special numeric values that stand for \t
        unknown/undefined (check in the "{data_file_descriptions}" for any such values, and \t
        consider also the "{outputs:data_exploration}").
        * Create new variables as needed.
        * Restrict the data based on exclusion/inclusion criteria (to match study goal, if applicable).
        * Standardize numeric values with different units into same-unit values.

        If no dataset preparations are needed, write below this header: \t
        `# No dataset preparations are needed.`


        `# DESCRIPTIVE STATISTICS`
        * In light of our study goals and the hypothesis testing plan (see above "{research_goal}" and \t
        "{hypothesis_testing_plan}"), decide whether and which descriptive statistics are needed to be included in \t
        the research paper and create a relevant table.

        For example:
        `## Table 0: "Descriptive statistics of height and age stratified by sex"`
        Write here the code to create a descriptive statistics dataframe `df0` and save it using:
        `df0.to_pickle('table_0.pkl')`

        If no descriptive statistics are needed, write: \t
        `# No descriptive statistics table is needed.`


        `# PREPROCESSING` 
        Perform any preprocessing steps needed to prepare the data for the analysis.
        For example, as applicable:
        * Creating dummy variables for categorical variables.
        * Any other data preprocessing you deem relevant.

        If no preprocessing is needed, write: \t
        `# No preprocessing is needed, because <your reasons here>.`


        `# ANALYSIS`
        Considering our "{research_goal}" and "{hypothesis_testing_plan}", decide on 1-3 tables \t
        (in addition to the above descriptive statistics, if any) we should create for our scientific paper. \t
        Typically, we should have at least one table for each hypothesis test.

        For each such scientific table:
        [a] Write a comment with a suggested table's caption. 
        Choose a caption that clearly describes the table's content and its purpose.
        For example:
        `## Table 1: "Test of association between age and risk of death, accounting for sex and race"`
        Avoid generic captions such as `## Table 1: "Results of analysis"`.

        [b] Perform analysis
        - Perform appropriate analysis and/or statistical tests (see above our "{hypothesis_testing_plan}").
        - Account for relevant confounding variables, as applicable.
        - Note that you may need to perform more than one test for each hypothesis.
        - Try using inherent functionality and syntax provided in functions from the available \t
        Python packages (above). Avoid, as possible, manually implementing generically available functionality.
        For example, to include interactions in regression analysis (if applicable), use the `formula = "y ~ a * b"` \t
        syntax in statsmodels formulas, rather than trying to manually multiply the variables.
        {mediation_note_if_applicable}\t

        [c] Create and save a dataframe representing the scientific table (`df1`, `df2`, etc): 
        * Only include information that is relevant and suitable for inclusion in a scientific table.
        * Nominal values should be accompanied by a measure of uncertainty (CI or STD and p-value).
        * Exclude data not important to the research goal, or that are too technical.
        * Do not repeat the same data in multiple tables.
        * The table should have labels for both the columns and the index (rows): 
            - As possible, do not invent new names; just keep the original variable names from the dataset.
            - As applicable, also keep any attr names from statistical test results.


        Overall, the section should have the following structure:

        `# ANALYSIS`
        `## Table 1: <your chosen table name here>`
        Write here the code to analyze the data and create a dataframe df1 for the table 1
        `df1.to_pickle('table_1.pkl')`

        `## Table 2: <your chosen table name here>`
        etc, up to 3 tables.


        # SAVE ADDITIONAL RESULTS
        At the end of the code, after completing the tables, create a dict containing any additional \t
        results you deem important to include in the scientific paper, and save it to a pkl file \t
        'additional_results.pkl'. 

        For example:

        `additional_results = {
            'Total number of observations': <xxx>,         
            'accuracy of <mode name> model': <xxx>,
            # etc, any other results and important parameters that are not included in the tables
        }
        with open('additional_results.pkl', 'wb') as f:
            pickle.dump(additional_results, f)
        `

        Avoid the following:
        Do not provide a sketch or pseudocode; write a complete runnable code including all '# HEADERS' sections.
        Do not create any graphics, figures or any plots.
        Do not send any presumed output examples.
        Avoid convoluted or indirect methods of data extraction and manipulation; \t
        For clarity, use direct attribute access for clarity and simplicity.
        For clarity, access dataframes using string-based column/index names, \t
        rather than integer-based column/index positions. 
        """)

    code_review_formatting_instructions: str = dedent_triple_quote_str("""
        Try to be as specific as possible when describing the issues and proposed fixes.
        Include in the dict as many issues as you find. 
        If you are sure that there are no issues, and the code and tables need no revision, \t
        then return an empty dict: `{}`. 
        """)

    code_review_prompts: Iterable[Tuple[str, bool, str]] = (
        (None, False, dedent_triple_quote_str("""
        Please follow these two steps:

        (1) Check your Python code and return a bullet-point response addressing these points (as applicable):

        * DATASET PREPARATIONS:
        - Missing values. If applicable, did we deal with missing, unknown, or undefined values, \t
        or with special numeric values that stand for unknown/undefined \t
        (check the "{data_file_descriptions}" for any such missing values)? 
        - Units. If applicable, did we correctly standardize numeric values with different units into same-unit values? 
        - Data restriction. If applicable, are we restricting the analysis to the correct part of the data \t
        (based on the study goal)?

        * DESCRIPTIVE STATISTICS:
        If applicable: 
        - Did we correctly report descriptive statistics? 
        - Is the choice of descriptive statistics and chosen variables contribute to the scope of study?
        - Is descriptive analysis done on the correct data (for example, before any data normalization steps)?

        * PREPROCESSING:
        Review the above "{data_file_descriptions}", then check our data preprocessing:
        - Are we performing any preprocessing steps that are not needed?
        - Are we missing any preprocessing steps that are needed?

        * ANALYSIS:
        As applicable, check for any data analysis issues, including: 
        - Analysis that should be performed on the preprocessed data is mistakenly performed on the original data.
        - Analysis that should be performed on the original data is mistakenly performed on the preprocessed data.
        - Incorrect choice of statistical test.
        - Imperfect implementation of statistical tests.
        - Did we correctly chose the variables that best represent the tested hypothesis? 
        - Are we accounting for relevant confounding variables (consult the "{data_file_descriptions}")?
        {regression_comments}\t
        {mediation_comments}\t
        {machine_learning_comments}\t
        {scipy_unpacking_comments}\t
        - Any other statistical analysis issues.

        (2) Based on your assessment above, return a Python Dict[str, str] mapping the issues you have noted 
        above (dict keys) to specific suggested corrections/improvements in the code (dict values).

        For example:
        ```python
        {
            "The model does not adequately account for confounding variables": \t
            "revise the code to add the following confounding variables ...",

            "The descriptive statistics is performed on the wrong data": \t
            "revise the code to perform the descriptive statistics on the preprocessed data.",
        }
        ```

        {code_review_formatting_instructions}
        """)),
        ('table_*.pkl', True, dedent_triple_quote_str("""
        I ran your code.

        Here is the content of the table '{filename}' that the code created for our scientific paper:

        {file_contents_str}

        Please review the table and follow these two steps:

        (1) Check the created table and return a bullet-point response addressing these points:
        * Sensible numeric values: Check each numeric value in the table and make sure it is sensible.
        For example:
        - If the table reports the mean of a variable, is the mean value sensible?
        - If the table reports CI, are the CI values flanking the mean?
        - Do values have correct signs?
        - Do you see any values that are not sensible (too large, too small)?
        - Do you see any 0 values that do not make sense?

        * Measures of uncertainty: If the table reports nominal values (like regression coefs), does \t
        it also report their measures of uncertainty (like p-value, CI, or STD, as applicable)?

        * Missing data: Are we missing key variables, or important results, that we should calculate and report? 

        * Any other issues you find.

        (2) Based on your assessment above, return a Python Dict[str, str] mapping the issues you have noted 
        above (dict keys) to specific suggested corrections/improvements in the code (dict values).

        For example:
        ```python
        {
            "Table {filename} reports incomplete results": \t
            "revise the code to add the following new column '<your suggested column name>'",

            "Table {filename} reports nominal values without measures of uncertainty": \t
            "revise the code to add STD and p-value.", 
        }
        ```

        {code_review_formatting_instructions}
        """)),
        ('*', False, dedent_triple_quote_str("""
        I ran your code.

        Here is the content of the file(s) that the code created for our scientific paper:

        {file_contents_str}

        Please review the code and theses output files and return a bullet-point response addressing these points:

        * Does the code create and output all needed results to address our {hypothesis_testing_plan}?

        * Sensible numeric values: Check each numeric value in the tables and in the additional results file \t
        and make sure it is sensible.
        For example: 
        - If a table reports the mean of a variable, is the mean value sensible?
        - If a table reports CI, are the CI values flanking the mean?
        - Do values have correct signs?
        - Do you see any values that are not sensible (too large, too small)?

        * Measures of uncertainty: If a table reports a nominal value (like mean of a variable), does \t
        it also report its measures of uncertainty (CI, or STD, as applicable)?

        * Missing data in a table: Are we missing key variables in a given table?

        {missing_tables_comments}
        * Any other issues you find.

        (2) Based on your assessment above, return a Python Dict[str, str] mapping the issues you have noted 
        above (dict keys) to specific suggested corrections/improvements in the code (dict values).

        For example:
        ```python
        {
            "A table is missing": \t
            "revise the code to add the following new table '<your suggested table caption>'",

            "Table <n> reports nominal values without measures of uncertainty": \t
            "revise the code to add STD and p-value.", 
        }
        ```

        {code_review_formatting_instructions}
        """)),
    )

    @staticmethod
    def _get_table_comments_for_code_and_output(code_and_output: CodeAndOutput) -> str:
        tables = code_and_output.created_files.get_created_content_files_to_contents(
            match_filename='table_*.pkl')
        num_tables = len(tables)
        # is_descriptive_table = 'table_0.pkl' in tables
        if num_tables == 0:
            return dedent_triple_quote_str("""
                * Missing tables: \t
                You did not create any tables. \t
                Note that research papers typically have 2 or more tables. \t
                Please suggest which tables to create and additional analysis needed.\n
                """)
        if num_tables == 1:
            return dedent_triple_quote_str("""
                * Missing tables: \t
                You only produced 1 table. \t
                Note that research papers typically have 2 or more tables. \t
                Are you sure all relevant tables are created? Can you suggest any additional analysis leading \t
                to additional tables?'\n
                """)
        if num_tables == 2:
            return dedent_triple_quote_str("""
                * Missing tables: \t
                Considering our research goal and hypothesis testing plan, \t
                are all relevant tables created? If not, can you suggest any additional tables?\n
                """)
        return ''

    def _get_specific_attrs_for_code_and_output(self, code_and_output: CodeAndOutput) -> Dict[str, str]:
        comments = super()._get_specific_attrs_for_code_and_output(code_and_output)
        comments['missing_tables_comments'] = self._get_table_comments_for_code_and_output(code_and_output)
        return comments

    @property
    def mediation_note_if_applicable(self):
        keywords = ['mediated', 'mediation', 'mediates', 'mediator', 'mediators']
        for hypothesis, plan in self.products.hypothesis_testing_plan.items():
            if any(keyword in hypothesis.lower() or keyword in plan.lower() for keyword in keywords):
                return dedent_triple_quote_str("""
                   - If you are doing a mediation analysis, don't forget to calculate both the 'a' and 'b' \t
                   paths (and add the same confounding variables to both paths, as needed).
                   """)
        return ""


@dataclass
class DataframePreventAssignmentToAttrs(PreventAssignmentToAttrs):
    obj_import_str: str = 'pandas.DataFrame'
    forbidden_set_attrs: Iterable[str] = ('columns', 'index')

    def _raise_exception(self, attr, value):
        raise RunIssue.from_current_tb(
            issue=f"To avoid mistakes, please do not directly assign to '{attr}'.",
            code_problem=CodeProblem.NonBreakingRuntimeIssue,
            instructions=f'Use instead `df.rename({attr}=<mapping>, inplace=True)`',
        )


@dataclass(frozen=True)
class TexTableContentOutputFileRequirement(TextContentOutputFileRequirement):
    filename: str = '*.tex'

    def get_referencable_text(self, content: Any, filename: str = None, num_file: int = 0,
                              content_view: ContentView = None) -> BaseReferenceableText:
        result = super().get_referencable_text(content, filename, num_file, content_view)
        if content_view == ContentViewPurpose.FINAL_INLINE:
            text = result.text
            first_line = text.split('\n')[0]
            if first_line.startswith(TABLE_COMMENT_HEADER):
                # we add a hyperlink to the table caption
                # extract the filename between `:
                pickle_filename = first_line.split('`')[1]
                pickle_filename = convert_str_to_latex_label(pickle_filename, 'file')
                # get the caption:
                caption = get_table_caption(text)
                new_caption = f'\\protect\\hyperlink{{{pickle_filename}}}{{{caption}}}'
                text = text.replace(caption, new_caption)
            result.text = text
        return result


tex_file_requirement = TexTableContentOutputFileRequirement('*.tex',
                                                            minimal_count=1, max_tokens=None,
                                                            hypertarget_prefixes=HypertargetPrefix.LATEX_TABLES.value)
tex_file_requirement.content_view_purpose_converter.view_purpose_to_params[
    ContentViewPurpose.FINAL_APPENDIX] = \
    ContentViewParams(hypertarget_format=HypertargetFormat(position=HypertargetPosition.NONE),
                      pvalue_on_str=OnStr.SMALLER_THAN)


@dataclass
class CreateLatexTablesCodeProductsGPT(BaseCreateTablesCodeProductsGPT):
    code_step: str = 'data_to_latex'
    debugger_cls: Type[DebuggerConverser] = TablesDebuggerConverser
    code_and_output_cls: Type[CodeAndOutput] = CreateLatexTablesCodeAndOutput
    headers_required_in_code: Tuple[str, ...] = (
        '# IMPORT',
        '# PREPARATION FOR ALL TABLES',
    )
    latex_document: LatexDocument = field(default_factory=LatexDocument)
    phrases_required_in_code: Tuple[str, ...] = \
        ('\nfrom my_utils import to_latex_with_note, is_str_in_df, split_mapping, AbbrToNameDef', )
    attrs_to_send_to_debugger: Tuple[str, ...] = \
        BaseCreateTablesCodeProductsGPT.attrs_to_send_to_debugger + ('latex_document', 'phrases_required_in_code', )
    user_agent: ScientificAgent = ScientificAgent.InterpretationReviewer
    background_product_fields: Tuple[str, ...] = \
        ('data_file_descriptions', 'research_goal', 'codes:data_preprocessing', 'codes:data_analysis',
         'created_files_content:data_analysis:table_?.pkl')
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
         'ReadPickleAttrReplacer': get_read_pickle_attr_replacer(),
         'PValueMessage': AttrReplacer(
             obj_import_str=PValue, attr='error_message_on_forbidden_func',
             wrapper="Calling `{func_name}` on a PValue object is forbidden.\n "
                     "Please use `format_p_value` instead."
        )}
    )

    output_file_requirements: OutputFileRequirements = OutputFileRequirements(
        [tex_file_requirement])

    provided_code: str = dedent_triple_quote_str('''
        def to_latex_with_note(df, filename: str, caption: str, label: str, \t
        note: str = None, legend: Dict[str, str] = None, **kwargs):
            """
            Converts a DataFrame to a LaTeX table with optional note and legend added below the table.

            Parameters:
            - df, filename, caption, label: as in `df.to_latex`.
            - note (optional): Additional note below the table.
            - legend (optional): Dictionary mapping abbreviations to full names.
            - **kwargs: Additional arguments for `df.to_latex`.
            """

        def is_str_in_df(df: pd.DataFrame, s: str):
            return any(s in level for level in getattr(df.index, 'levels', [df.index]) + \t
        getattr(df.columns, 'levels', [df.columns]))

        AbbrToNameDef = Dict[Any, Tuple[Optional[str], Optional[str]]]

        def split_mapping(abbrs_to_names_and_definitions: AbbrToNameDef):
            abbrs_to_names = {abbr: name for abbr, (name, definition) in \t
        abbrs_to_names_and_definitions.items() if name is not None}
            names_to_definitions = {name or abbr: definition for abbr, (name, definition) in \t
        abbrs_to_names_and_definitions.items() if definition is not None}
            return abbrs_to_names, names_to_definitions
        ''')

    user_initiation_prompt: str = dedent_triple_quote_str('''
        Please write a Python code to convert and re-style the "table_?.pkl" dataframes created \t
        by our "{codes:data_analysis}" into latex tables suitable for our scientific paper.

        Your code should use the following 3 custom functions provided for import from `my_utils`: 

        ```python
        {provided_code}
        ```

        Your code should:

        * Rename column and row names: You should provide a new name to any column or row label that is abbreviated \t
        or technical, or that is otherwise not self-explanatory.

        * Provide legend definitions: You should provide a full definition for any name (or new name) \t
        that satisfies any of the following: 
        - Remains abbreviated, or not self-explanatory, even after renaming.
        - Is an ordinal/categorical variable that requires clarification of the meaning of each of its possible values.
        - Contains unclear notation, like '*' or ':'
        - Represents a numeric variable that has units, that need to be specified.        

        To avoid re-naming mistakes, you should define for each table a dictionary, \t
        `mapping: AbbrToNameDef`, which maps any original \t
        column and row names that are abbreviated or not self-explanatory to an optional new name, \t
        and an optional definition.
        If different tables share several common labels, then you can build a `shared_mapping`, \t
        from which you can extract the relevant labels for each table.

        Overall, the code must have the following structure:

        ```python
        # IMPORT
        import pandas as pd
        from my_utils import to_latex_with_note, is_str_in_df, split_mapping, AbbrToNameDef

        # PREPARATION FOR ALL TABLES
        # <As applicable, define a shared mapping for labels that are common to all tables. For example:>
        shared_mapping: AbbrToNameDef = {
            'AvgAge': ('Avg. Age', 'Average age, years'),
            'BT': ('Body Temperature', '1: Normal, 2: High, 3: Very High'),
            'W': ('Weight', 'Participant weight, kg'),
            'MRSA': (None, 'Infected with Methicillin-resistant Staphylococcus aureus, 1: Yes, 0: No'),
            ...: (..., ...),
        }
        # <This is of course just an example. Consult with the "{data_file_descriptions}" \t
        and the "{codes:data_analysis}" for choosing the labels and their proper scientific names \t
        and definitions.>

        # TABLE {first_table_number}:
        df{first_table_number} = pd.read_pickle('table_{first_table_number}.pkl')

        # FORMAT VALUES <include this sub-section only as applicable>
        # <Rename technical values to scientifically-suitable values. For example:>
        df{first_table_number}['MRSA'] = df{first_table_number}['MRSA'].apply(lambda x: 'Yes' if x == 1 else 'No')

        # RENAME ROWS AND COLUMNS <include this sub-section only as applicable>
        # <Rename any abbreviated or not self-explanatory table labels to scientifically-suitable names.>
        # <Use the `shared_mapping` if applicable. For example:>
        mapping{first_table_number} = dict((k, v) for k, v in shared_mapping.items() \t
        if is_str_in_df(df{first_table_number}, k)) 
        mapping{first_table_number} |= {
            'PV': ('P-value', None),
            'CI': (None, '95% Confidence Interval'),
            'Sex_Age': ('Age * Sex', 'Interaction term between Age and Sex'),
        }
        abbrs_to_names{first_table_number}, legend{first_table_number} = split_mapping(mapping{first_table_number})
        df{first_table_number} = df{first_table_number}.rename(columns=abbrs_to_names{first_table_number}, \t
        index=abbrs_to_names{first_table_number})

        # SAVE AS LATEX:
        to_latex_with_note(
            df{first_table_number}, 'table_{first_table_number}.tex',
            caption="<choose a caption suitable for a table in a scientific paper>", 
            label='table:<chosen table label>',
            note="<If needed, add a note to provide any additional information that is not captured in the caption>",
            legend=legend{first_table_number})


        # TABLE <?>:
        # <etc, all 'table_?.pkl' files>
        ```

        Avoid the following:
        Do not provide a sketch or pseudocode; write a complete runnable code including all '# HEADERS' sections.
        Do not create any graphics, figures or any plots.
        Do not send any presumed output examples.
        ''')

    code_review_prompts: Iterable[Tuple[str, bool, str]] = ()

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
    rewind_after_getting_a_valid_response: Optional[Rewind] = Rewind.ACCUMULATE
    should_remove_citations_from_section: bool = True
    section_names: Tuple[str, ...] = ('Code Explanation',)

    def __post_init__(self):
        self.background_product_fields = self.background_product_fields + ('codes:' + self.code_step,)
        BaseScientificPostCodeProductsHandler.__post_init__(self)
        LatexReviewBackgroundProductsConverser.__post_init__(self)

    user_initiation_prompt: str = dedent_triple_quote_str("""
        Please return a triple-backtick Latex Block explaining what the code above does. 
        Do not provide a line-by-line explanation, rather provide a \t
        high-level explanation of the code in a language suitable for a Methods section of a research \t
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
        Importantly: do NOT explain the content of columns that are already explained for the \t
        original dataset (see above DESCRIPTION OF THE DATASET).
        """)

    requesting_explanation_for_a_modified_dataframe: str = dedent_triple_quote_str("""
        Explain the content of all the new or modified columns of "{dataframe_file_name}".

        Return your explanation as a dictionary, where the keys are the column names {columns}, \t 
        and the values are the strings that explain the content of each column.

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
