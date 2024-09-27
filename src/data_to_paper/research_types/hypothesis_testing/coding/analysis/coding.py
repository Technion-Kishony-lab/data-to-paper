from dataclasses import dataclass
from typing import Tuple, List, Optional, Dict, Any, Type, Collection

from pathlib import Path

from data_to_paper.base_steps import DebuggerConverser
from data_to_paper.base_steps.request_code import CodeReviewPrompt
from data_to_paper.code_and_output_files.code_and_output import CodeAndOutput
from data_to_paper.code_and_output_files.file_view_params import ViewPurpose
from data_to_paper.code_and_output_files.output_file_requirements import \
    OutputFileRequirements, PickleContentOutputFileRequirement
from data_to_paper.code_and_output_files.referencable_text import LabeledNumericReferenceableText, \
    convert_str_to_latex_label
from data_to_paper.llm_coding_utils import describe_df, df_to_figure, df_to_latex
from data_to_paper.research_types.hypothesis_testing.cast import ScientificAgent
from data_to_paper.research_types.hypothesis_testing.check_df_to_funcs.df_checker import check_analysis_df
from data_to_paper.research_types.hypothesis_testing.env import get_max_rows_and_columns
from data_to_paper.run_gpt_code.code_runner import CodeRunner
from data_to_paper.run_gpt_code.overrides.dataframes.df_with_attrs import InfoDataFrameWithSaveObjFuncCall
from data_to_paper.research_types.hypothesis_testing.coding.analysis.utils import get_pickle_dump_attr_replacer
from data_to_paper.research_types.hypothesis_testing.coding.base_code_conversers import BaseTableCodeProductsGPT
from data_to_paper.research_types.hypothesis_testing.coding.utils import create_pandas_and_stats_contexts
from data_to_paper.research_types.hypothesis_testing.scientific_products import HypertargetPrefix
from data_to_paper.run_gpt_code.extract_and_check_code import ModifyAndCheckCodeExtractor, CodeExtractor
from data_to_paper.run_gpt_code.overrides.dataframes.utils import df_to_string_with_format_value, \
    format_numerics_and_iterables
from data_to_paper.run_gpt_code.overrides.pvalue import is_containing_p_value, OnStr, OnStrPValue
from data_to_paper.run_gpt_code.run_issues import RunIssue, CodeProblem
from data_to_paper.text import dedent_triple_quote_str
from data_to_paper.utils.nice_list import NiceDict


@dataclass(frozen=True)
class BaseDataFramePickleContentOutputFileRequirement(PickleContentOutputFileRequirement):
    referenceable_text_cls: type = LabeledNumericReferenceableText
    output_folder: Optional[Path] = None  # where the figures will be saved

    def _is_figure(self, content: InfoDataFrameWithSaveObjFuncCall) -> bool:
        return content.get_func_call().func == df_to_figure

    def _plot_kind(self, content: InfoDataFrameWithSaveObjFuncCall) -> Optional[str]:
        if not self._is_figure(content):
            return None
        return content.get_func_call().kwargs.get('kind')

    def _get_content_and_header_for_product(
            self, content: InfoDataFrameWithSaveObjFuncCall, filename: str = None, num_file: int = 0, level: int = 3,
            view_purpose: ViewPurpose = ViewPurpose.PRODUCT):
        func_name = content.get_func_call().func_name
        content, header = super()._get_content_and_header_for_product(content, filename, num_file, level, view_purpose)
        header += f' (with {func_name})'
        return content, header

    def _convert_content_to_labeled_text(self, content: InfoDataFrameWithSaveObjFuncCall, filename: str = None,
                                         num_file: int = 0, view_purpose: ViewPurpose = None) -> str:
        with OnStrPValue(self._convert_view_purpose_to_pvalue_on_str(view_purpose)):
            return describe_df(
                content, should_format=True,
                max_rows_and_columns_to_show=get_max_rows_and_columns(is_figure=self._is_figure(content),
                                                                      kind=self._plot_kind(content),
                                                                      to_show=True))

    def _get_content_and_header_for_app_html(
            self, content: InfoDataFrameWithSaveObjFuncCall, filename: str = None, num_file: int = 0, level: int = 3,
            view_purpose: ViewPurpose = ViewPurpose.APP_HTML):
        func_call = content.get_func_call()
        with OnStrPValue(self._convert_view_purpose_to_pvalue_on_str(view_purpose)):
            html = func_call.call(is_html=True, figure_folder=self.output_folder)
        return html, f'<h{level}>{filename}</h{level}>'

    def get_code_line_str_for_file(self, filename: str, content: InfoDataFrameWithSaveObjFuncCall) -> Optional[str]:
        func_call = content.get_func_call()
        func = func_call.func
        table_or_figure = 'Table' if func == df_to_latex else 'Figure'
        return f'## {table_or_figure} {func_call.filename}:'

    def get_hyperlink_label_for_file_header(self, filename: str,
                                            content: InfoDataFrameWithSaveObjFuncCall) -> Optional[str]:
        source_file = content.get_prior_filename()
        if source_file:
            return convert_str_to_latex_label(source_file + '.pkl', prefix='file')
        return super().get_hyperlink_label_for_file_header(filename, content)

    def get_issues_for_output_file_content(self, filename: str, content: Any) -> List[RunIssue]:
        issues = super().get_issues_for_output_file_content(filename, content)
        issues.extend(self._check_df(content))
        return issues

    def _check_df(self, content: InfoDataFrameWithSaveObjFuncCall) -> List[RunIssue]:
        return []


@dataclass(frozen=True)
class DataFramePickleContentOutputFileRequirement(BaseDataFramePickleContentOutputFileRequirement):
    def _check_df(self, content: InfoDataFrameWithSaveObjFuncCall) -> List[RunIssue]:
        return check_analysis_df(content, output_folder=self.output_folder)

    def _get_content_and_header_for_final_appendix(
            self, content: InfoDataFrameWithSaveObjFuncCall, filename: str = None, num_file: int = 0, level: int = 3,
            view_purpose: ViewPurpose = ViewPurpose.FINAL_APPENDIX):
        with OnStrPValue(OnStr.WITH_ZERO):
            content = df_to_string_with_format_value(content)
        return content, f'% {filename}'


class DictPickleContentOutputFileRequirement(PickleContentOutputFileRequirement):

    def _convert_content_to_labeled_text(self, content: Any, filename: str = None, num_file: int = int,
                                         view_purpose: ViewPurpose = None) -> str:
        content = NiceDict(content, format_numerics_and_iterables=format_numerics_and_iterables)
        return super()._convert_content_to_labeled_text(content, filename, num_file, view_purpose)

    def get_code_line_str_for_file(self, filename: str, content: Any) -> Optional[str]:
        return '# SAVE ADDITIONAL RESULTS'

    def get_issues_for_output_file_content(self, filename: str, content: Any) -> List[RunIssue]:
        # all checks are done in _pickle_dump_with_checks
        return super().get_issues_for_output_file_content(filename, content)


class StaticChecks(ModifyAndCheckCodeExtractor):
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

    def get_issues_for_static_code_check(self, code: str) -> List[RunIssue]:
        issues = super().get_issues_for_static_code_check(code)

        for class_name, from_formula in self.class_and_from_formula:
            if class_name + '(' in code:
                issues.append(RunIssue(
                    category='Coding: good practices',
                    issue=f'You are using the `{class_name}` class. ',
                    instructions=dedent_triple_quote_str(f"""
                        You should use the `{from_formula}` function instead, so that the formula is clearly \t
                        specified as a string. 
                        Reminder: For interactions, if any, use the `*` operator in the formula, rather than \t
                        manually multiplying the variables.
                        """),
                    code_problem=CodeProblem.StaticCheck,
                ))

        return issues


@dataclass
class DataAnalysisDebuggerConverser(DebuggerConverser):

    def _get_issues_for_created_output_files(self, code_and_output: CodeAndOutput, contexts) -> List[RunIssue]:
        """
        Check that a PValue instance appear in at least one of the created tables.
        """
        issues = super()._get_issues_for_created_output_files(code_and_output, contexts)
        if issues:
            return issues
        issues = self.get_issues_for_missing_p_values(code_and_output)
        if issues:
            return issues
        return self._get_issues_for_df_comments(code_and_output, contexts)

    def get_issues_for_missing_p_values(self, code_and_output: CodeAndOutput) -> List[RunIssue]:
        issues = []
        any_pvalues = False
        for names_to_contents in code_and_output.created_files.values():
            for content in names_to_contents.values():
                if is_containing_p_value(content):
                    any_pvalues = True
                    break
        if not any_pvalues:
            issues.append(RunIssue(
                category='Statistics: good practices',
                issue='We are presenting results for a statistical-testing paper, but no p-values are reported in '
                      'any of the created files.',
                instructions='Please revise the code to perform statistical tests and report p-values in the tables.',
                code_problem=CodeProblem.OutputFileContentA,
            ))
        return issues

    def _get_issues_for_df_comments(self, code_and_output: CodeAndOutput, contexts) -> List[RunIssue]:
        issues = []
        files_to_requirements_and_contents = \
            code_and_output.created_files.get_created_files_to_requirements_and_contents(
                match_filename='df_*.pkl', is_content=True)
        for df_file_name, (requirement, content) in files_to_requirements_and_contents.items():
            df_header = requirement.get_code_line_str_for_file(df_file_name, content)
            if df_header and df_header not in code_and_output.code:
                issues.append(RunIssue(
                    category="Code structure",
                    issue=f'Your code is missing a comment "{df_header}".',
                    instructions=dedent_triple_quote_str("""
                        Please make sure all saved tables/figures have a comment with their chosen tag.
                        This comment should be placed at the beginning of the section of the code that creates \t
                        the table/figure. Like this:

                        ```python
                        ...

                        ## Table df_tag1:
                        caption = "..."
                        ...  # any analysis code related to df_tag1
                        df_tag1 = ...
                        df_to_latex(df_tag1, 'df_tag1', caption=caption)

                        ## Figure df_tag2:
                        caption = "..."
                        ...  # any analysis code related to df_tag2
                        df_tag2 = ...
                        df_to_figure(df_tag2, 'df_tag2', caption=caption)

                        ...
                        ```

                        If you are creating multiple tables in the same code section, '
                        you should precede this section with a separate comment for each of the tables.
                        Like this:

                        ```python
                        ...

                        ## Table df_tag1:
                        caption1 = "..."                        
                        ## Figure df_tag2:
                        caption2 = "..."

                        ...  # any analysis code related to both df_tag1 and df_tag2
                        df_tag1 = ...
                        df_to_latex(df_tag1, 'df_tag1', caption=caption1)
                        df_tag2 = ...
                        df_to_figure(df_tag2, 'df_tag2', caption=caption2)

                        ...
                        ```
                        """),
                    code_problem=CodeProblem.OutputFileAnnotation,
                ))
        return issues


@dataclass
class AnalysisCodeRunner(CodeRunner):
    modified_imports: Tuple[Tuple[str, Optional[str]]] = CodeRunner.modified_imports + (
        ('my_utils', 'data_to_paper.research_types.hypothesis_testing.coding.analysis.my_utils'),
    )


@dataclass
class DataAnalysisCodeProductsGPT(BaseTableCodeProductsGPT):
    code_step: str = 'data_analysis'
    code_extractor_cls: Type[CodeExtractor] = StaticChecks
    debugger_cls: Type[DebuggerConverser] = DataAnalysisDebuggerConverser
    code_runner_cls: Type[CodeRunner] = AnalysisCodeRunner
    headers_required_in_code: Tuple[str, ...] = (
        '# IMPORT',
        '# LOAD DATA',
        '# DATASET PREPARATIONS',
        '# DESCRIPTIVE STATISTICS',
        '# PREPROCESSING',
        '# ANALYSIS',
        '# SAVE ADDITIONAL RESULTS',
    )
    max_debug_iterations_per_attempt: int = 20
    max_code_revisions: int = 3
    user_agent: ScientificAgent = ScientificAgent.Debugger

    background_product_fields: Tuple[str, ...] = \
        ('data_file_descriptions', 'outputs:data_exploration', 'codes:data_preprocessing',
         'created_files_headers:data_preprocessing', 'research_goal', 'hypothesis_testing_plan')
    background_product_fields_to_hide_during_code_revision: Tuple[str, ...] = \
        ('outputs:data_exploration', 'research_goal')
    allow_data_files_from_sections: Tuple[Optional[str]] = (None, 'data_preprocessing')

    supported_packages: Tuple[str, ...] = ('pandas', 'numpy', 'scipy', 'statsmodels', 'sklearn', 'pickle')

    def _create_output_file_requirements(self) -> OutputFileRequirements:
        return OutputFileRequirements(
            [DataFramePickleContentOutputFileRequirement('df_*.pkl', 1, output_folder=self.output_directory),
             DictPickleContentOutputFileRequirement('additional_results.pkl', 1,
                                                    hypertarget_prefixes=HypertargetPrefix.ADDITIONAL_RESULTS.value)
             ])

    provided_code: str = dedent_triple_quote_str('''
            {df_to_latex_doc}

            {df_to_figure_doc}
        ''')

    df_to_latex_extra_vars: str = ''
    df_to_latex_extra_vars_explain: str = ''
    df_to_figure_extra_latex_vars: str = ''
    df_to_figure_extra_latex_vars_explain: str = ''
    df_to_figure_extra_plot_vars: str = ''
    df_to_figure_extra_plot_vars_explain: str = ''

    mission_prompt: str = dedent_triple_quote_str("""
        Write a complete Python code to analyze the data according to our \t
        "{research_goal}" and "{hypothesis_testing_plan}". 

        The code should create scientific Tables and Figures for our paper. 
        It should use the following provided functions:

        ```python
        {provided_code}
        ```

        The code must have the following structure (with these exact capitalized headers):

        `# IMPORT`
        `from my_utils import df_to_latex, df_to_figure`
        `import pickle`
        You can also import here any other packages including: 
        {supported_packages}\t

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

        If no dataset preparations are needed, write below this header:
        `# No dataset preparations are needed.`

        `# DESCRIPTIVE STATISTICS`
        * In light of our study goals and the hypothesis testing plan (see above "{research_goal}" and \t
        "{hypothesis_testing_plan}"), decide whether and which descriptive statistics displayitems are needed.

        - If you decide that no descriptive statistics is needed, write:
        `# No descriptive statistics table is needed because <your reasons here>.` 

        - For descriptive statistics Table:
        `## Table df_desc_stat:`
        `caption = "Descriptive statistics of ..."`
        Write here the code to create a descriptive statistics dataframe `df_desc_stat`.
        Then, save the dataframe and create LaTeX:
        df_to_latex(df_desc_stat, 'df_desc_stat', caption=caption)

        - For descriptive statistics figure:
        `## Figure df_desc_stat:`
        `caption = "Descriptive statistics of ..."`
        `df_desc_stat = ...`
        `df_desc_stat['ci_low'] = df_desc_stat['mean'] - 1.96 * df_desc_stat['std'] / np.sqrt(df_desc_stat['count'])`
        `df_desc_stat['ci_high'] = ...`
        `df_to_figure(df_desc_stat, 'df_desc_stat', kind='bar', y=['mean'], y_ci=[('ci_low', 'ci_high')])`

        Note: Showing variables of different units in the same figure is not a good practice. \t
        Use a table instead.

        `# PREPROCESSING` 
        Perform any preprocessing steps needed to prepare the data for the analysis.
        For example, as applicable:
        * Creating dummy variables for categorical variables.
        * Any other data preprocessing you deem relevant.

        If no preprocessing is needed, write:
        `# No preprocessing is needed, because <your reasons here>.`

        # ANALYSIS
        Considering our "{research_goal}" and "{hypothesis_testing_plan}", decide on 1-3 additional displayitems \t
        (tables/figures) we should create for our scientific paper.
        Typically, we should have at least one displayitem for each hypothesis test.

        For each such displayitem, follow these 4 steps:
        [a] Write a comment with a unique label and add the table/figure caption. 
        Example for a table:
        `## Table df_age_death:` 
        `caption = "Test of association between age and risk of death, accounting for sex and race"`
        Example for a figure:
        `## Figure df_longevity_factors:` 
        `caption = "Adjusted and unadjusted odds ratios for longevity ..."`

        [b] Perform analysis
        - Perform appropriate analysis and/or statistical tests (see above our "{hypothesis_testing_plan}").
        - Account for relevant confounding variables, as applicable.
        - Note that you may need to perform more than one test for each hypothesis.
        - Try using inherent functionality and syntax provided in functions from the available \t
        Python packages (above).
        - Avoid, as possible, manually implementing generically available functionality. \t
        For example, to include interactions in regression analysis (if applicable), use the `formula = "y ~ a * b"` \t
        syntax in statsmodels formulas, rather than trying to manually multiply the variables.
        {mediation_note_if_applicable}\t

        [c] Create a dataframe for the scientific table/figure. 
        * Only include information that is relevant and suitable for inclusion in a scientific table/figure.
        * Nominal values should be accompanied by a measure of uncertainty (CI or STD and p-value).
        * As applicable, CI should be provided as a column of tuple (lower, upper).
        * Exclude data not important to the research goal, or that are too technical.
        * Do not repeat the same data in multiple tables/figures.
        * The df should have labels for both the columns and the index (rows): 
          - As possible, do not invent new names; just keep the original variable names from the dataset.
          - As applicable, also keep any attr names from statistical test results.

        [d] Convert the dataframe to LaTeX Table or figure using the provided functions.


        Overall, the analysis section should have the following structure:

        `# ANALYSIS`
        For each hypothesis test, create 1-3 display items (tables/figures):

        For a table:
        `## Table df_tag:`  tag is a short unique label, like 'df_age_death'
        caption = "<chosen table caption>"
        Write here code to analyze the data and create a dataframe `df_tag` for the table. 
        `df_to_latex(df_tag, 'df_tag', caption=caption)`

        For a figure:
        `## Figure df_tag:`
        caption = "<chosen figure caption>"
        Write here code to analyze the data and create a dataframe `df_tag` for the figure.
        `df_to_figure(df_tag, 'df_tag', caption=caption, kind='bar', 
        y=['height_avg', 'weight_avg', ...], 
        y_ci=['height_ci', 'weight_ci', ...],  \t
        # or y_ci=[('height_ci_low', 'height_ci_high'), ('weight_ci_low', 'weight_ci_high'), ...]
        y_p_value=['height_pval', 'weight_pval', ...])`

        etc, up to 3-4 display items in total.

        # SAVE ADDITIONAL RESULTS
        At the end of the code, after completing the tables, create a dict containing any additional \t
        results you deem important to include in the scientific paper, and save it to a pkl file \t
        'additional_results.pkl'. 

        For example:
        ```python
        additional_results = {
            'Total number of observations': <xxx>,         
            'accuracy of <mode name> model': <xxx>,
            # etc, any other results and important parameters that are not included in the displayitems
        }
        with open('additional_results.pkl', 'wb') as f:
            pickle.dump(additional_results, f)
        ```

        Avoid the following:
        Do not provide a sketch or pseudocode; write a complete runnable code including all '# HEADERS' sections.
        Do not directly use matplotlib or other plotting packages; only use the provided functions.
        Do not send any presumed output examples.
        Avoid convoluted or indirect methods of data extraction and manipulation; \t
        For clarity, use direct attribute access for clarity and simplicity.
        For clarity, access dataframes using string-based column/index names, \t
        rather than integer-based column/index positions.
        """)

    code_review_prompts: Collection[CodeReviewPrompt] = (
        CodeReviewPrompt('code flaws', None, False, dedent_triple_quote_str("""
        The code runs without any obvious bugs, but I am worried that it may have some fundamental \t
        mathematical or statistical flaws.
        I will need you to carefully check the Python code for possible flaws.
        {code_review_formatting_instructions}

        ### CHECK FOR FUNDAMENTAL FLAWS:
        Check for any fundamental mathematical or statistical flaws in the code.

        ### CHECK FOR WRONG CALCULATIONS:
        Explicitly list all key calculation in the code and look carefully for any mistakes.
        You should directly cut and paste the key calculations from the code, and carefully assess them.

        ### CHECK FOR MATH TRIVIALITIES:
        Check for any mathematically trivial assessments / statistical tests.

        ### OTHER ISSUES:
        Any other issues you find in the code.

        For each of these categories, you can provide one or more issues. 
        For example:

        ```{python_or_json}
        {
            "The analysis of <analysis name>": ["OK", "It is correct to ... "],
            "The analysis of <other analysis name>": ["CONCERN", "Forgot to include ..."],
            "The analysis of xxx vs yyy": ["CONCERN", "Different units were not standardized"],

            "mean_signal = np.mean(signal)": ("OK", "The mean is calculated correctly"],
            "sem_signal = np.std(signal)": ["CONCERN", "Forgot to divide by sqrt(n)"],
            "formula = 'y ~ a : b + c'": ["CONCERN", "The formula accounts for the interaction between a and b \t
        but does not include their main effects"],  

            "The test of positivity of mean(z)": ["CONCERN", "By definition, all z values are positive, so \t
        the mean is triviality positive"],
            "The test A > B": ["CONCERN", "In our case, this is always true because B is negative and A is positive"],
            "The test C > 0": ["OK", "This is a valid test because ..."],

            "<Any other issues you find>": ["CONCERN", "<Issue description>"],
            "<Any other assertion>": ["OK", "<Assertion description>"],
            "etc": ["OK/CONCERN", "..."],
        }
        ```

        {code_review_notes}
        """)),
        CodeReviewPrompt('data handling', None, False, dedent_triple_quote_str("""
        The code runs without any obvious bugs, but I am worried that it may contain some flaws in the analysis. 
        I will need you to carefully check the Python code for possible issues.
        {code_review_formatting_instructions}

        ### DATASET PREPARATIONS:
        - Missing values. If applicable, did we deal with missing, unknown, or undefined values,
        or with special numeric values that stand for unknown/undefined?
        Check the "{data_file_descriptions}" for any such missing values.
        - Units. If applicable, did we correctly standardize numeric values with different units 
        into same-unit values?
        - Data restriction. If applicable, are we restricting the analysis to the correct part of the data
        (based on the {hypothesis_testing_plan})?

        ### DESCRIPTIVE STATISTICS:
        As applicable, check for issues in the descriptive statistics.

        ### PREPROCESSING:
        Review the above "{data_file_descriptions}", then check our data preprocessing.
        Are we performing all needed preprocessing steps? Are we mistakenly performing any unneeded steps?

        ### ANALYSIS:        
        As applicable, check for any data analysis issues. For instance, \t
        verify that each analysis is done on the relevant data.

        ### STATISTICAL TESTS:
        Check the choice and implementation of statistical tests.

        For each of these categories, you can provide one or more issues. 
        For example:

        ```{python_or_json}
        {
            "Missing values": ["OK", "We correctly dealt with missing values"],
            "Standardizing units": ["CONCERN", "In the comparison of x and y, different units were not standardized"],
            "Data restriction": ["OK", "No data restriction is needed. We are correctly using all data"],  

            "Descriptive statistics: presented if needed": ["OK", "The code does not create a descriptive statistics \t
        table, but this is ok because ..."],
            "Descriptive statistics: variable choice": ["CONCERN", "We should not have included xxx in the table ..."],
            "Descriptive statistics: Correct data": ["CONCERN", "We mistakenly reported descriptive statistics on the \t
        data after normalization"],

            "Preprocessing": ["CONCERN", "We have normalized all variables, but xxx should not be normalized"],

            "Analysis on correct data": ["CONCERN", "We mistakenly performed the xxx analysis \t
        on the preprocessed data. This step should have been done on the original data"],

            "Choice of statistical test": ["CONCERN", "We should have used ttt test instead of sss test, because ..."],
            "Implementation of statistical test <test name>": ["OK", "The implementation is correct, because ..."],
        {regression_comments}\t
        {mediation_comments}\t
        {machine_learning_comments}\t
        }
        ```

        {code_review_notes}
        """)),
        CodeReviewPrompt('"{filename}"', 'df_*.pkl', True, dedent_triple_quote_str("""
        I ran your code.

        Here is the content of the table '{filename}' that the code created for our scientific paper:

        {file_contents_str}

        Please review the table and return a list of point-by-point assessments.

        {code_review_formatting_instructions}

        Check the following:
        ### SENSIBLE NUMERIC VALUES:
        Check each numeric value in the table and make sure it is sensible.

        ### MEASURES OF UNCERTAINTY: 
        If the table reports nominal values (like regression coefs), 
        does it also report their measures of uncertainty (like p-value, CI, or STD, as applicable)?

        ### MISSING DATA: 
        Are we missing key variables, or important results, that we should calculate and report in the table?

        ### OTHER ISSUES:
        Any other issues you find in the table.

        For each of these categories, you can provide one or more issues. 
        For example:

        ```{python_or_json}
        {
            "Sensible values": ["OK", "All the values in the table are sensible"],
            "Order of magnitude": ["CONCERN", "Weight values of 10^3 are not sensible"], 
            "CI of variables": ["CONCERN", "The CI values of 'xxx' are not flanking the mean of 'xxx'"],
            "Sign of values": ["CONCERN", "Height cannot be negative, but we have negative values"],
            "Zero values": ["CONCERN", "We have zero values for ..., but this is not possible"],

            "Measures of uncertainty": ["CONCERN", "We should have included p-values for ..."],
            "Measures of uncertainty": ["CONCERN", "CI should be provided as a column of (lower, upper) tuple"],

            "Missing data": ["CONCERN", "To fit with our hypothesis testing plan, we should have included ..."], 

            "<Any other issues you find>": ["CONCERN", "<Issue description>"],
            "<Any other assertion>": ["OK", "<Assertion description>"],
            "etc": ["OK/CONCERN", "..."],
        }
        ```

        {code_review_notes}
        """)),
        CodeReviewPrompt('all created files', '*', False, dedent_triple_quote_str("""
        I ran your code.

        Here is the content of the file(s) that the code created for our scientific paper:

        {file_contents_str}

        Please carefully review the code and these output files and return a point by point assessment.

        {code_review_formatting_instructions}:

        ### COMPLETENESS OF TABLES:
        Does the code create and output all needed results to address our {hypothesis_testing_plan}?

        ### CONSISTENCY ACROSS TABLES:
        Are the tables consistent in terms of the variables included, the measures of uncertainty, etc?

        ### MISSING DATA: 
        Are we missing key variables in a given table? Are we missing measures of uncertainty 
        (like p-value, CI, or STD, as applicable)?

        For each of these categories, you can provide one or more issues. 
        For example:

        ```{python_or_json}
        {
            "Completeness of output": ["OK", "We should include the P-values for the test in df_?.pkl"],

            "Consistency among tables": ["CONCERN", "In df_1.pkl, we provide age in years, but in df_2.pkl, \t
        we provide age in months"],

            "Missing data": ["CONCERN", "We have to add the variable 'xxx' to df_?.pkl"],
            "Measures of uncertainty": ["CONCERN", "We should have included p-values for ..."],
        {missing_tables_comments}
        }
        ```

        {code_review_notes}
        """)),
    )

    def _get_additional_contexts(self) -> Optional[Dict[str, Any]]:
        return create_pandas_and_stats_contexts(allow_dataframes_to_change_existing_series=None,
                                                enforce_saving_altered_dataframes=False,
                                                issue_if_statistics_test_not_called=True) | {
                'PickleDumpAttrReplacer': get_pickle_dump_attr_replacer(),
        }

    @staticmethod
    def _get_df_comments_for_code_and_output(code_and_output: CodeAndOutput) -> str:
        dfs = code_and_output.created_files.get_created_content_files_to_contents(
            match_filename='df_*.pkl')
        num_dfs = len(dfs)
        # is_descriptive_df = 'df_0.pkl' in dfs
        if num_dfs == 0:
            return dedent_triple_quote_str("""
                # * MISSING TABLES:
                # Note that the code does not create any tables.
                # Research papers typically have 2 or more tables. \t
                # Please suggest which tables to create and additional analysis needed.
                "Missing tables": ["CONCERN", "I suggest creating tables for ..."]""", indent=4)
        if num_dfs == 1:
            return dedent_triple_quote_str("""
                # * MISSING TABLES:
                # The code only creates 1 table.
                # Research papers typically have 2 or more tables. \t
                # Are you sure all relevant tables are created? Can you suggest any additional analysis leading \t
                to additional tables?
                "Missing tables": ["CONCERN", "I suggest creating an extra table for showing ..."]""", indent=4)
        if num_dfs == 2:
            return dedent_triple_quote_str("""
                # * MISSING TABLES:
                # Considering our research goal and hypothesis testing plan,
                # are all relevant tables created? If not, can you suggest any additional tables?
                "Missing tables": ["CONCERN", "I suggest creating an extra table showing ..."]""", indent=4)
        return ''

    @property
    def mediation_note_if_applicable(self):
        keywords = ['mediated', 'mediation', 'mediates', 'mediator', 'mediators']
        if not self.products or not self.products.hypothesis_testing_plan:
            return ""
        for hypothesis, plan in self.products.hypothesis_testing_plan['HYPOTHESES'].items():
            if any(keyword in hypothesis.lower() or keyword in plan.lower() for keyword in keywords):
                return dedent_triple_quote_str("""
                   - If you are doing a mediation analysis, don't forget to calculate both the 'a' and 'b' \t
                   paths (and add the same confounding variables to both paths, as needed).
                   """)
        return ""

    @staticmethod
    def _get_regression_comments_for_code_and_output(code_and_output: CodeAndOutput) -> str:
        if 'statsmodels' not in code_and_output.code:
            return ''
        linear_regression_funcs = ['ols(', 'OLS(', 'logit(', 'Logit(', 'glm(', 'GLM(']
        code = code_and_output.code
        func_names = [func for func in linear_regression_funcs if func in code]
        if not func_names:
            return ''
        return dedent_triple_quote_str("""\n
            # - In regressions, in case interactions terms are included:
            # Is the main effect adequately included in the model with interaction terms?
            # Did we use the `*` operator in statsmodels formula as recommended?
            # (as applicable, better use `formula = "y ~ a * b"`, instead of trying to \t
            manually multiply the variables)
            # For example:
            "Model with interaction terms": 
                ["CONCERN", "We forgot to include the main effect in the xxx model, \t
            please use the `*` operator in the formula"]
            """, indent=4)

    @staticmethod
    def _get_mediation_comments_for_code_and_output(code_and_output: CodeAndOutput) -> str:
        if 'mediation' not in code_and_output.code.lower() and False:
            return ''
        return dedent_triple_quote_str("""\n
            # - In mediation analysis:
            # did we calculate the mediation effect (e.g., using the Sobel test or other)?
            # did we account for relevant confounding factors?
            # (by adding these same confounding factors to both the 'a' and 'b' paths)
            # For example:
            "Mediation analysis":
                ["CONCERN", "We did not explicitly calculate the mediation effect"]
            """, indent=4)

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
        return dedent_triple_quote_str("""\n
            # - Machine-Learning models:
            # Are we adequately performing hyperparameter tuning using cross-validation (as appropriate). 
            # Are the best hyperparameters reported (either in a table file or in the "additional_results.pkl" file).
            # For example:
            "Hyperparameter tuning":
                ["CONCERN", "We forgot to perform hyperparameter tuning"]
            """, indent=4)

    def _get_specific_attrs_for_code_and_output(self, code_and_output: CodeAndOutput) -> Dict[str, str]:
        comments = super()._get_specific_attrs_for_code_and_output(code_and_output)
        comments['regression_comments'] = self._get_regression_comments_for_code_and_output(code_and_output)
        comments['mediation_comments'] = self._get_mediation_comments_for_code_and_output(code_and_output)
        comments['machine_learning_comments'] = self._get_machine_learning_comments_for_code_and_output(code_and_output)
        comments['missing_tables_comments'] = self._get_df_comments_for_code_and_output(code_and_output)
        return comments
