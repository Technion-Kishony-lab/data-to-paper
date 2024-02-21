from dataclasses import dataclass, field
from typing import Tuple, List, Optional, Dict, Any, Iterable, Type

from data_to_paper.base_steps import DebuggerConverser
from data_to_paper.code_and_output_files.code_and_output import CodeAndOutput
from data_to_paper.code_and_output_files.output_file_requirements import TextContentOutputFileRequirement, \
    NumericTextContentOutputFileRequirement, OutputFileRequirements, PickleContentOutputFileRequirement
from data_to_paper.research_types.scientific_research.coding.base_code_conversers import \
    BaseScientificCodeProductsGPT, BaseCreateTablesCodeProductsGPT
from data_to_paper.research_types.scientific_research.coding.utils import get_additional_contexts
from data_to_paper.research_types.scientific_research.coding.utils_modified_for_gpt_use.to_pickle import \
    get_dataframe_to_pickle_attr_replacer, get_pickle_dump_attr_replacer
from data_to_paper.research_types.scientific_research.scientific_products import HypertargetPrefix
from data_to_paper.run_gpt_code.overrides.dataframes.df_methods import STR_FLOAT_FORMAT
from data_to_paper.run_gpt_code.overrides.dataframes.df_methods.methods import temporarily_change_float_format
from data_to_paper.run_gpt_code.overrides.pvalue import is_containing_p_value
from data_to_paper.run_gpt_code.run_issues import RunIssue, CodeProblem
from data_to_paper.utils import dedent_triple_quote_str
from data_to_paper.utils.nice_list import NiceList, NiceDict


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
    def get_code_header_for_file(self, filename: str) -> Optional[str]:
        # 'table_*.pkl' -> '# Table *'
        if filename.startswith('table_') and filename.endswith('.pkl'):
            return f'## Table {filename[6:-4]}'
        # 'additional_results.pkl' -> '# Additional Results'
        if filename == 'additional_results.pkl':
            return '# SAVE ADDITIONAL RESULTS'
        return None


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
        issues = []
        for table_file_name in code_and_output.created_files.get_created_content_files(match_filename='table_*.pkl'):
            table_header = code_and_output.get_code_header_for_file(table_file_name)
            if table_header not in code_and_output.code:
                issues.append(RunIssue(
                    category="Each saved table should have a header comment with the table name.\n",
                    issue=f'Your code is missing a comment "{table_header}".',
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
        BaseScientificCodeProductsGPT.attrs_to_send_to_debugger + ('headers_required_in_code',)

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
        default_factory=lambda: get_additional_contexts(
            allow_dataframes_to_change_existing_series=False,
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
        The code runs ok, but I am worried that it may contain some fundamental mathematical or statistical \t
        flaws. To check for such flaws, I will need you to carefully follow these two steps:

        (1) Deeply check your Python code for any fundamental coding/mathematical/statistical flaws \t
        and return a bullet-point response addressing these points (as applicable):
        
        * WRONG FORMULA:
        - List all key mathematical formulas used in the code and indicate for each one if it is correct, \t
        or if it should be revised. 

        * TRIVIALLY-TRUE STATISTICAL TESTS:
        Are there any statistical tests that are mathematically trivial? Like:
        - testing whether the mean of all values above 0 is above 0.
        - comparing distributions that have different underlying scales (or different ranges), \t
        and which were not properly normalized.
        - testing whether the mean of X + Y is larger than the mean of X, when Y is positive.
        - etc, any other tests that you suspect are trivial.
        
        * OTHER:
        Any other mathematical or statistical issues that you can identify.

        (2) Based on your assessment above, return a Python Dict[str, str] mapping the issues you have noted 
        above (dict keys) to specific suggested corrections/improvements in the code (dict values).

        For example:
        ```python
        {
            "The formula for the regression model is incorrect": \t
            "revise the code to use the following formula: ...",
            "The statistical test for association of ... and ... is trivial": \t
            "revise the code to perform the following more meaningful test: ...",
        }
        ```

        {code_review_formatting_instructions}
        """)),
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
