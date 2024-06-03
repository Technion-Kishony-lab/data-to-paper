from dataclasses import dataclass
from typing import Tuple, List, Optional, Dict, Any, Type, Collection

from pandas import DataFrame

from data_to_paper.base_steps import DebuggerConverser
from data_to_paper.base_steps.request_code import CodeReviewPrompt
from data_to_paper.code_and_output_files.code_and_output import CodeAndOutput
from data_to_paper.code_and_output_files.file_view_params import ViewPurpose
from data_to_paper.code_and_output_files.output_file_requirements import \
    NumericTextContentOutputFileRequirement, OutputFileRequirements, PickleContentOutputFileRequirement
from data_to_paper.research_types.hypothesis_testing.coding.base_code_conversers import BaseCreateTablesCodeProductsGPT
from data_to_paper.research_types.hypothesis_testing.coding.utils import get_additional_contexts
from data_to_paper.research_types.hypothesis_testing.coding.utils_modified_for_gpt_use.to_pickle import \
    get_dataframe_to_pickle_attr_replacer, get_pickle_dump_attr_replacer
from data_to_paper.research_types.hypothesis_testing.scientific_products import HypertargetPrefix
from data_to_paper.run_gpt_code.extract_and_check_code import ModifyAndCheckCodeExtractor, CodeExtractor
from data_to_paper.run_gpt_code.overrides.dataframes.utils import to_string_with_format_value, \
    format_numerics_and_iterables
from data_to_paper.run_gpt_code.overrides.pvalue import is_containing_p_value
from data_to_paper.run_gpt_code.run_issues import RunIssue, CodeProblem
from data_to_paper.utils import dedent_triple_quote_str
from data_to_paper.utils.nice_list import NiceDict


class DataFramePickleContentOutputFileRequirement(PickleContentOutputFileRequirement):
    def _to_str(self, content: DataFrame, view_purpose: ViewPurpose, **kwargs) -> str:
        return to_string_with_format_value(content)


class DictPickleContentOutputFileRequirement(PickleContentOutputFileRequirement):
    def _to_str(self, content: DataFrame, view_purpose: ViewPurpose, **kwargs) -> str:
        content = NiceDict(content, format_numerics_and_iterables=format_numerics_and_iterables)
        return super()._to_str(content, view_purpose, **kwargs)


@dataclass
class DataAnalysisCodeAndOutput(CodeAndOutput):
    def get_code_header_for_file(self, filename: str) -> Optional[str]:
        # 'df_*.pkl' -> '# DF *'
        if filename.startswith('df_') and filename.endswith('.pkl'):
            return f'## DF {filename[3:-4]}'
        # 'additional_results.pkl' -> '# Additional Results'
        if filename == 'additional_results.pkl':
            return '# SAVE ADDITIONAL RESULTS'
        return None


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
class DataAnalysisDebuggerConverser(DebuggerConverser):

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
                category='Statistics: good practices',
                issue='We are presenting results for a statistical-testing paper, but no p-values are reported in '
                      'any of the created files.',
                instructions='Please revise the code to perform statistical tests and report p-values in the tables.',
                code_problem=CodeProblem.OutputFileContentLevelA,
            ))
        if issues:
            return issues
        return self._get_issues_for_df_comments(code_and_output, contexts)

    def _get_issues_for_df_comments(self, code_and_output: CodeAndOutput, contexts) -> List[RunIssue]:
        issues = []
        for df_file_name in code_and_output.created_files.get_created_content_files(match_filename='df_*.pkl'):
            df_header = code_and_output.get_code_header_for_file(df_file_name)
            if df_header not in code_and_output.code:
                issues.append(RunIssue(
                    category="Code structure",
                    issue=f'Your code is missing a comment "{df_header}".',
                    instructions='Please make sure all saved tables have a header comment with the table name.\n'
                                 'If you are creating multiple tables in the same section of the code, '
                                 'you should precede this section with a separate comment for each of the tables.',
                    code_problem=CodeProblem.OutputFileContentLevelA,
                ))
        return issues


@dataclass
class DataAnalysisCodeProductsGPT(BaseCreateTablesCodeProductsGPT):
    code_step: str = 'data_analysis'
    code_extractor_cls: Type[CodeExtractor] = StaticChecks
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

    background_product_fields: Tuple[str, ...] = \
        ('data_file_descriptions', 'outputs:data_exploration', 'codes:data_preprocessing',
         'created_files_headers:data_preprocessing', 'research_goal', 'hypothesis_testing_plan')
    background_product_fields_to_hide_during_code_revision: Tuple[str, ...] = \
        ('outputs:data_exploration', 'research_goal')
    allow_data_files_from_sections: Tuple[Optional[str]] = (None, 'data_preprocessing')

    supported_packages: Tuple[str, ...] = ('pandas', 'numpy', 'scipy', 'statsmodels', 'sklearn', 'pickle')

    output_file_requirements: OutputFileRequirements = OutputFileRequirements(
        [DataFramePickleContentOutputFileRequirement('df_?.pkl', 1),
         DictPickleContentOutputFileRequirement('additional_results.pkl', 1,
                                                hypertarget_prefixes=HypertargetPrefix.ADDITIONAL_RESULTS.value)
         ])

    mission_prompt: str = dedent_triple_quote_str("""
        Write a complete Python code to analyze the data and create dataframes as basis for scientific Tables \t
        and Figures for our paper.

        Created df for tables will be later converted to LaTeX tables using `df.to_latex()`.
        Created df for figures will be later converted to plots using a `my_plot(df, x=, y=, ...)` function, \t
        which is similar to `df.plot()` but also allows specifying:
        - Confidence intervals (CI) for error bars. Like:
        `my_plot(df, x=, y='height', y_ci='height_ci', ...)`
        where 'height_ci' is a column in the df with the CI values as a tuple (lower, upper).
        - P-values for plotting significance as stars. Like:
        `my_plot(df, x=, y='height', y_p_value='height_pval', ...)`
        where 'height_pval' is a column in the df with the p-values.

        Important: We are not making the plots in this code, only creating dataframes that will be used later to \t
        create the plots and tables. 

        The code must have the following sections (with these exact capitalized headers):

        `# IMPORT`
        `import pickle`
        You can also import here any other packages including: 
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

        If no dataset preparations are needed, write below this header:
        `# No dataset preparations are needed.`


        `# DESCRIPTIVE STATISTICS`
        * In light of our study goals and the hypothesis testing plan (see above "{research_goal}" and \t
        "{hypothesis_testing_plan}"), decide whether and which descriptive statistics are needed to be included in \t
        the research paper and create dfs for relevant tables and figures.

        For example:
        `## DF 0: "Table: Descriptive statistics of height and age stratified by sex"`
        `# Designed for creating a scientific table using: df0.to_latex()`
        Write here the code to create a descriptive statistics dataframe `df0`.
        Do not convert to latex yet. Just save it using:
        `df0.to_pickle('df_0.pkl')`
        If no descriptive statistics are needed, write:
        `# No descriptive statistics table is needed.`

        And/or, for a figure:
        `## DF 1: "Figure: Distribution of height"`
        `# Designed for creating a scientific figure using: my_plot(df1, kind='hist', x='height')`
        Write here the code to create `df1`. Like, `df1 = data_after_cleaning['height']`.
        Do not create the plot yet. Just save the dataframe using:
        `df1.to_pickle('df_1.pkl')`

        `# PREPROCESSING` 
        Perform any preprocessing steps needed to prepare the data for the analysis.
        For example, as applicable:
        * Creating dummy variables for categorical variables.
        * Any other data preprocessing you deem relevant.

        If no preprocessing is needed, write:
        `# No preprocessing is needed, because <your reasons here>.`


        `# ANALYSIS`
        Considering our "{research_goal}" and "{hypothesis_testing_plan}", decide on 1-3 additional displayitems \t
        (tables/figures) we should create for our scientific paper. \t
        Typically, we should have at least one table or figure for each hypothesis test.

        For each such displayitem, follow these 3 steps:
        [a] Write a comment with a suggested table/figure caption. 
        For example:
        `## DF 1: "Table: Test of association between age and risk of death, accounting for sex and race"`
        Or
        `## DF 1: "Figure: Adjusted and unadjusted odds ratios for ..."  
        Avoid generic captions such as `## DF 1: "Results of analysis"`.

        [b] Perform analysis
        - Perform appropriate analysis and/or statistical tests (see above our "{hypothesis_testing_plan}").
        - Account for relevant confounding variables, as applicable.
        - Note that you may need to perform more than one test for each hypothesis.
        - Try using inherent functionality and syntax provided in functions from the available \t
        Python packages (above). 
        - Avoid, as possible, manually implementing generically available functionality.
        For example, to include interactions in regression analysis (if applicable), use the `formula = "y ~ a * b"` \t
        syntax in statsmodels formulas, rather than trying to manually multiply the variables.
        {mediation_note_if_applicable}\t

        [c] Create and save a dataframe for the scientific table/figure (`df1`, `df2`, etc): 
        * Only include information that is relevant and suitable for inclusion in a scientific table.
        * Nominal values should be accompanied by a measure of uncertainty (CI or STD and p-value).
        As applicable, CI should be provided as a column of tuple (lower, upper).
        * Exclude data not important to the research goal, or that are too technical.
        * Do not repeat the same data in multiple tables/figures.
        * The df should have labels for both the columns and the index (rows): 
            - As possible, do not invent new names; just keep the original variable names from the dataset.
            - As applicable, also keep any attr names from statistical test results.


        Overall, the section should have the following structure:

        `# ANALYSIS`
        `## DF 1: "Table: <your chosen table name here>"`
        `# Intended use: df1.to_latex()`
        Write here the code to analyze the data and create a dataframe df1 for table 1
        `df1.to_pickle('df_1.pkl')`

        `## DF 2: "Figure: <your chosen figure name here>"`
        `# Intended use: my_plot(df2, kind='bar', y=['height', 'weight', ...], y_ci=['height_ci', 'weight_ci', ...],
        y_p_value=['height_pval', 'weight_pval', ...])`
        Write here the code to analyze the data and create a dataframe df2 for figure 2.
        Do not create the plot yet. Just save the dataframe using:
        `df2.to_pickle('df_2.pkl')`

        etc, up to 3-4 display items.


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
        Do not create the actual plots or latex tables; only prepare and save the suitable dataframes.
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

        For example:
        ```python
        {
            # * CHECK FOR FUNDAMENTAL FLAWS:
            # Check for any fundamental mathematical or statistical flaws in the code.
            # For example:
            "The analysis of <analysis name>": ("OK", "It is correct to ... "),
            "The analysis of <other analysis name>": ("CONCERN", "Forgot to include ..."),
            "The analysis of xxx vs yyy": ("CONCERN", "Different units were not standardized"),

            # * CHECK FOR WRONG CALCULATIONS:
            # Explicitly list all key calculation in the code and look carefully for any mistakes.
            # You should directly cut and paste the key calculations from the code, and carefully assess them.           
            # For example:
            "mean_signal = np.mean(signal)": ("OK", "The mean is calculated correctly"),
            "sem_signal = np.std(signal)": ("CONCERN", "Forgot to divide by sqrt(n)"),
            "formula = 'y ~ a : b + c'": ("CONCERN", "The formula accounts for the interaction between a and b
            but does not include their main effects"),  

            # * CHECK FOR MATH TRIVIALITIES:
            # Check for any mathematically trivial assessments / statistical tests.
            # For example:
            "The test of positivity of mean(z)": ("CONCERN", "By definition, all z values are positive, so \t
        the mean is triviality positive"),
            "The test A > B": ("CONCERN", "In our case, this is always true because B is negative and A is positive"),
            "The test C > 0": ("OK", "This is a valid test because ..."),
        }
        ```

        {code_review_notes}
        """)),
        CodeReviewPrompt('data handling', None, False, dedent_triple_quote_str("""
        The code runs without any obvious bugs, but I am worried that it may contain some flaws in the analysis. 
        I will need you to carefully check the Python code for possible issues.
        {code_review_formatting_instructions}

        For example:
        ```python
        {
            # * DATASET PREPARATIONS:
            # - Missing values. If applicable, did we deal with missing, unknown, or undefined values,
            # or with special numeric values that stand for unknown/undefined?
            # Check the "{data_file_descriptions}" for any such missing values.
            # For example:
            "Missing values": ("OK", "We correctly dealt with missing values"),

            # - Units. If applicable, did we correctly standardize numeric values with different units 
            # into same-unit values?
            # For example:
            "Standardizing units": ("CONCERN", "In the comparison of x and y, different units were not standardized"),

            # - Data restriction. If applicable, are we restricting the analysis to the correct part of the data
            # (based on the {hypothesis_testing_plan})?
            # For example:
            "Data restriction": ("OK", "No data restriction is needed. We are correctly using all data"),  

            # * DESCRIPTIVE STATISTICS:
            # As applicable, check for issues in the descriptive statistics.
            # For example:
            "Descriptive statistics: presented if needed": ("OK", "The code does not create a descriptive statistics \t
        table, but this is ok because ..."),
            "Descriptive statistics: variable choice": ("CONCERN", "We should not have included xxx in the table ..."),
            "Descriptive statistics: Correct data": ("CONCERN", "We mistakenly reported descriptive statistics on the \t
        data after normalization"),

            # * PREPROCESSING:
            # Review the above "{data_file_descriptions}", then check our data preprocessing.
            # Are we performing all needed preprocessing steps? Are we mistakenly performing any unneeded steps?
            # For example:
            "Preprocessing": ("CONCERN", "We have normalized all variables, but xxx should not be normalized"),

            # * ANALYSIS:        
            # As applicable, check for any data analysis issues, including:

            # - Each analysis is done on the relevant data.
            # For example:
            "Analysis on correct data": ("CONCERN", "We mistakenly performed the xxx analysis \t
        on the preprocessed data. This step should have been done on the original data"),

            # - Choice and implementation of statistical tests.
            # For example:
            "Choice of statistical test": ("CONCERN", "We should have used ttt test instead of sss test, because ..."),
            "Implementation of statistical test <test name>": ("OK", "The implementation is correct, because ..."),
        {regression_comments}\t
        {mediation_comments}\t
        {machine_learning_comments}\t
        {scipy_unpacking_comments}\t
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

        For example:
        ```python
        {
            # * SENSIBLE NUMERIC VALUES:
            # Check each numeric value in the table and make sure it is sensible.
            # For example:
            "Sensible values": ("OK", "All the values in the table are sensible"),
            "Order of magnitude": ("CONCERN", "Weight values of 10^3 are not sensible"), 
            "CI of variables": ("CONCERN", "The CI values of 'xxx' are not flanking the mean of 'xxx'"),
            "Sign of values": ("CONCERN", "Height cannot be negative, but we have negative values"),
            "Zero values": ("CONCERN", "We have zero values for ..., but this is not possible"),

            # * MEASURES OF UNCERTAINTY: 
            # If the table reports nominal values (like regression coefs), 
            # does it also report their measures of uncertainty (like p-value, CI, or STD, as applicable)?
            # For example:
            "Measures of uncertainty": ("CONCERN", "We should have included p-values for ..."),
            Or:
            "Measures of uncertainty": ("CONCERN", "CI should be provided as a column of (lower, upper) tuple"),

            # * MISSING DATA: 
            # Are we missing key variables, or important results, that we should calculate and report in the table?
            # For example:
            "Missing data": ("CONCERN", "To fit with our hypothesis testing plan, we should have included ..."), 
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

        for example:
        ```python
        {
            # * COMPLETENESS OF TABLES:
            # Does the code create and output all needed results to address our {hypothesis_testing_plan}?
            # For example:
            "Completeness of output": ("OK", "We should include the P-values for the test in df_?.pkl"),

            # * CONSISTENCY ACROSS TABLES:
            # Are the tables consistent in terms of the variables included, the measures of uncertainty, etc?
            # For example:
            "Consistency among tables": ("CONCERN", "In df_1.pkl, we provide age in years, but in df_2.pkl, \t
        we provide age in months"),

            # * MISSING DATA: 
            # Are we missing key variables in a given table? Are we missing measures of uncertainty 
            # (like p-value, CI, or STD, as applicable)?
            # For example:
            "Missing data": ("CONCERN", "We have to add the variable 'xxx' to df_?.pkl"),
            "Measures of uncertainty": ("CONCERN", "We should have included p-values for ..."),

        {missing_tables_comments}
        }
        ```

        {code_review_notes}
        """)),
    )

    def _get_additional_contexts(self) -> Optional[Dict[str, Any]]:
        return get_additional_contexts(
            allow_dataframes_to_change_existing_series=False,
            enforce_saving_altered_dataframes=False,
            issue_if_statistics_test_not_called=True) | {
                'ToPickleAttrReplacer': get_dataframe_to_pickle_attr_replacer(),
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
                "Missing tables": ("CONCERN", "I suggest creating tables for ...")""", indent=4)
        if num_dfs == 1:
            return dedent_triple_quote_str("""
                # * MISSING TABLES:
                # The code only creates 1 table.
                # Research papers typically have 2 or more tables. \t
                # Are you sure all relevant tables are created? Can you suggest any additional analysis leading \t
                to additional tables?
                "Missing tables": ("CONCERN", "I suggest creating an extra table for showing ...")""", indent=4)
        if num_dfs == 2:
            return dedent_triple_quote_str("""
                # * MISSING TABLES:
                # Considering our research goal and hypothesis testing plan,
                # are all relevant tables created? If not, can you suggest any additional tables?
                "Missing tables": ("CONCERN", "I suggest creating an extra table showing ...")""", indent=4)
        return ''

    def _get_specific_attrs_for_code_and_output(self, code_and_output: CodeAndOutput) -> Dict[str, str]:
        comments = super()._get_specific_attrs_for_code_and_output(code_and_output)
        comments['missing_tables_comments'] = self._get_df_comments_for_code_and_output(code_and_output)
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
