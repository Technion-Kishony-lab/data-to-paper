from dataclasses import dataclass
from typing import Iterable, Any, Type, Tuple, Optional, Dict, Collection, List

from data_to_paper.base_steps import DebuggerConverser
from data_to_paper.base_steps.request_code import CodeReviewPrompt
from data_to_paper.code_and_output_files.code_and_output import CodeAndOutput
from data_to_paper.code_and_output_files.file_view_params import ViewPurpose
from data_to_paper.code_and_output_files.output_file_requirements import OutputFileRequirements
from data_to_paper.code_and_output_files.ref_numeric_values import HypertargetFormat, HypertargetPosition, \
    ReferencedValue
from data_to_paper.code_and_output_files.referencable_text import convert_str_to_latex_label
from data_to_paper.latex.latex_doc import LatexDocument
from data_to_paper.research_types.hypothesis_testing.cast import ScientificAgent
from data_to_paper.research_types.hypothesis_testing.coding.base_code_conversers import BaseTableCodeProductsGPT
from data_to_paper.research_types.hypothesis_testing.coding.utils import create_pandas_and_stats_contexts
from data_to_paper.research_types.hypothesis_testing.scientific_products import HypertargetPrefix, ScientificProducts
from data_to_paper.run_gpt_code.attr_replacers import PreventAssignmentToAttrs, PreventCalling, AttrReplacer
from data_to_paper.run_gpt_code.code_runner import CodeRunner
from data_to_paper.run_gpt_code.overrides.dataframes.df_with_attrs import InfoDataFrameWithSaveObjFuncCall
from data_to_paper.run_gpt_code.overrides.pvalue import PValue, OnStr, OnStrPValue
from data_to_paper.run_gpt_code.run_issues import RunIssue, CodeProblem
from data_to_paper.text import dedent_triple_quote_str

from ..analysis.coding import BaseDataFramePickleContentOutputFileRequirement, DataAnalysisDebuggerConverser
from ...check_df_to_funcs.df_checker import check_displayitem_df


@dataclass
class DataframePreventAssignmentToAttrs(PreventAssignmentToAttrs):
    obj_import_str: str = 'pandas.DataFrame'
    forbidden_set_attrs: Iterable[str] = ('columns', 'index')

    def _raise_exception(self, attr, value):
        raise RunIssue.from_current_tb(
            category='Coding: good practices',
            issue=f"To avoid mistakes, please do not directly assign to '{attr}'.",
            code_problem=CodeProblem.NonBreakingRuntimeIssue,
            instructions=f'Use instead `df.rename({attr}=<mapping>, inplace=True)`',
        )


@dataclass(frozen=True)
class TexDisplayitemContentOutputFileRequirement(BaseDataFramePickleContentOutputFileRequirement):
    hypertarget_prefixes: Optional[Tuple[str]] = HypertargetPrefix.LATEX_TABLES.value
    latex_document: Optional[LatexDocument] = None

    def _check_df(self, content: InfoDataFrameWithSaveObjFuncCall) -> List[RunIssue]:
        return check_displayitem_df(content, output_folder=self.output_folder, latex_document=self.latex_document)

    def _convert_view_purpose_to_pvalue_on_str(self, view_purpose: ViewPurpose) -> OnStr:
        return OnStr.SMALLER_THAN

    def _get_hyper_target_format(self, content: InfoDataFrameWithSaveObjFuncCall, filename: str = None,
                                 num_file: int = 0, view_purpose: ViewPurpose = None) -> HypertargetFormat:
        if self._is_figure(content):
            if view_purpose == ViewPurpose.FINAL_INLINE:
                return HypertargetFormat()
            if view_purpose == ViewPurpose.FINAL_APPENDIX:
                return HypertargetFormat(position=HypertargetPosition.ADJACENT, raised=True, escaped=True)
        else:
            if view_purpose == ViewPurpose.FINAL_INLINE:
                return HypertargetFormat(position=HypertargetPosition.ADJACENT, raised=True, escaped=False)
            if view_purpose == ViewPurpose.FINAL_APPENDIX:
                return HypertargetFormat()

        return super()._get_hyper_target_format(content, filename, num_file, view_purpose)

    def _get_block_label(self, filename: str, num_file: int, view_purpose: ViewPurpose) -> str:
        return 'latex'

    def _convert_content_to_labeled_text(self, content: InfoDataFrameWithSaveObjFuncCall, filename: str = None,
                                         num_file: int = 0, view_purpose: ViewPurpose = None) -> str:
        func, args, kwargs = content.get_func_call()
        pvalue_on_str = self._convert_view_purpose_to_pvalue_on_str(view_purpose)
        if view_purpose == ViewPurpose.FINAL_INLINE:
            caption = kwargs.get('caption', '')
            caption_lines = caption.split('\n')
            first_line = caption_lines[0]
            filename = content.get_prior_filename()
            first_line = r"\protect" + ReferencedValue(
                value=first_line,
                label=convert_str_to_latex_label(filename + '.pkl', prefix='file'),
                is_target=False).to_str(HypertargetFormat(position=HypertargetPosition.WRAP))
            caption_lines[0] = first_line
            kwargs = kwargs.copy()
            kwargs['caption'] = '\n'.join(caption_lines)

        with OnStrPValue(pvalue_on_str):
            return func(*args, **kwargs, should_format=True)

    def _get_content_and_header_for_final_inline(
            self, content: InfoDataFrameWithSaveObjFuncCall, filename: str = None, num_file: int = 0, level: int = 3,
            view_purpose: ViewPurpose = ViewPurpose.FINAL_INLINE):
        text, header_refs = self.get_formatted_text_and_header_references(content, filename, num_file, view_purpose)
        return text, f'% {filename}\n' + '\n'.join(header_ref.to_str() for header_ref in header_refs)


@dataclass
class UtilsCodeRunner(CodeRunner):
    modified_imports: Tuple[Tuple[str, Optional[str]]] = CodeRunner.modified_imports + (
        ('my_utils', 'data_to_paper.research_types.hypothesis_testing.coding.displayitems.my_utils'),
    )


@dataclass
class DisplayitemsDebuggerConverser(DataAnalysisDebuggerConverser):
    products: ScientificProducts = None

    def _get_issues_for_missing_dfs(self, code_and_output: CodeAndOutput) -> List[RunIssue]:
        created_pkl_df_files = self.products.get_created_dfs()
        required_tex_files = [file.replace('.pkl', '.tex') for file in created_pkl_df_files]
        created_tex_files = code_and_output.created_files.get_created_content_files()
        missing_tex_files = set(required_tex_files) - set(created_tex_files)
        if len(missing_tex_files):
            return [RunIssue(
                category='Missing output files',
                issue=f"You did not create a tex file for the following tables: {missing_tex_files}",
                instructions=f"Please create a tex file for each table.",
                code_problem=CodeProblem.OutputFileCallingSyntax,
            )]
        return []

    def _get_issues_for_created_output_files(self, code_and_output: CodeAndOutput, contexts) -> List[RunIssue]:
        issues = super()._get_issues_for_created_output_files(code_and_output, contexts)
        if issues:
            return issues
        return self._get_issues_for_missing_dfs(code_and_output)

    def _get_issues_for_df_comments(self, code_and_output: CodeAndOutput, contexts) -> List[RunIssue]:
        return []  # TODO: Implement this method


@dataclass
class CreateDisplayitemsCodeProductsGPT(BaseTableCodeProductsGPT):
    COPY_ATTRIBUTES = ('latex_document', )
    latex_document: LatexDocument = None
    code_step: str = 'data_to_latex'
    debugger_cls: Type[DebuggerConverser] = DisplayitemsDebuggerConverser
    code_runner_cls: Type[CodeRunner] = UtilsCodeRunner
    headers_required_in_code: Tuple[str, ...] = (
        '# IMPORT',
        '# PREPARATION FOR ALL TABLES AND FIGURES',
    )
    phrases_required_in_code: Tuple[str, ...] = \
        ('\nfrom my_utils import df_to_latex, df_to_figure, is_str_in_df, split_mapping, AbbrToNameDef', )

    max_debug_iterations_per_attempt: int = 20
    max_code_revisions: int = 1
    user_agent: ScientificAgent = ScientificAgent.InterpretationReviewer
    background_product_fields: Tuple[str, ...] = \
        ('data_file_descriptions', 'research_goal', 'codes:data_preprocessing', 'codes:data_analysis',
         'created_files_content:data_analysis:df_*.pkl')
    allow_data_files_from_sections: Tuple[Optional[str]] = ('data_analysis', )
    supported_packages: Tuple[str, ...] = ('pandas', 'numpy', 'my_utils')

    def _create_output_file_requirements(self) -> OutputFileRequirements:
        return OutputFileRequirements([
            TexDisplayitemContentOutputFileRequirement(
                'df_*_formatted.pkl', minimal_count=1,
                output_folder=self.output_directory,
                latex_document=self.latex_document)
        ])

    provided_code: str = dedent_triple_quote_str('''
        {df_to_latex_doc}

        {df_to_figure_doc}

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

    mission_prompt: str = dedent_triple_quote_str('''
        Please write a Python code to convert and re-style the "df_*.pkl" dataframes created \t
        by our "{codes:data_analysis}" into nicer latex tables/figures suitable for our scientific paper.

        Your code should use the following 4 custom functions provided for import from `my_utils`: 

        ```python
        {provided_code}
        ```

        Your code should define `all_mapping: AbbrToNameDef`, which maps any original \t
        column and row names that are abbreviated or not self-explanatory to an optional new name, \t
        and an optional definition.

        Then, for each df_*.pkl file, your code should:

        * Rename column and row names: You should provide a new name to any column or row label that is abbreviated \t
        or technical, or that is otherwise not self-explanatory.

        * Provide glossary definitions: You should provide a full definition for any original name \t
        (or modified new name) in the df that satisfies any of the following: 
        - Remains abbreviated, or not self-explanatory, even after renaming.
        - Is an ordinal/categorical variable that requires clarification of the meaning of each of its possible values.
        - Contains unclear notation, like '*' or ':', '_'.
        - Represents a numeric variable that has units, that need to be specified.        

        To avoid re-naming mistakes, you should define for each df a dictionary, \t
        `mapping: AbbrToNameDef`, derived from `all_mapping`, that contains only the labels that are in the df \t
        (use the `is_str_in_df` function). 

        Overall, the code must have the following structure (### are my instructions, not part of the code):

        ```python
        # IMPORT
        import pandas as pd
        from my_utils import df_to_latex, df_to_figure, is_str_in_df, split_mapping, AbbrToNameDef

        # PREPARATION FOR ALL TABLES AND FIGURES
        ### Define mapping for all df labels that need to be renamed and/or glossary defined. For example:
        all_mapping: AbbrToNameDef = {
            # Rename and provide glossary definitions for any abbreviated or not self-explanatory labels:
            'AvgAge': ('Avg. Age', 'Average age, years'),
            'BT': ('Body Temperature', '1: Normal, 2: High, 3: Very High'),

            # Explain and add units:
            'Weight': ('Weight', 'Participant weight, kg'),

            # Provide a full definition for any label that is not self-explanatory:
            'MRSA': ('MRSA', 'Infected with Methicillin-resistant Staphylococcus aureus, 1: Yes, 0: No'),

            # If the table is too wide, provide a shorter label:
            'Too Long Label': ('Short Label', 'Definition of the short label'),

            # Etc.
            ...: (..., ...),
        }
        ### These are of course just examples. 
        ### Consult with the "{data_file_descriptions}" and the "{codes:data_analysis}" 
        ### for choosing the actual labels and their proper scientific names and definitions.

        ## Process df_tag:  
        ### `tag` is a placeholder for the actual name of the df created by the {codes:data_analysis}
        df_tag = pd.read_pickle('df_tag.pkl')

        # Format values:
        ### If not needed, write '# Not Applicable' under the '# Format values:' header.
        ### Rename technical values to scientifically-suitable values. For example:
        df_tag['MRSA'] = df_tag['MRSA'].apply(lambda x: 'Yes' if x == 1 else 'No')

        # Rename rows and columns:
        ### Rename any abbreviated or not self-explanatory df labels to scientifically-suitable names.
        ### Get from the `all_mapping` the labels that are in the focal df:
        mapping = dict((k, v) for k, v in all_mapping.items() if is_str_in_df(df_mrsa_age, k))
        ### If needed, add/change df-specific `mapping` \t
        (typically, `mapping` should be a subset of `all_mapping`, so this step might not be needed). 
        mapping |= {
            'PV': ('P-value', None),
            'CI': ('CI', '95% Confidence Interval'),
            'Sex_Age': ('Age * Sex', 'Interaction term between Age and Sex'),
        }
        abbrs_to_names, glossary = split_mapping(mapping)
        df_tag.rename(columns=abbrs_to_names, index=abbrs_to_names, inplace=True)

        ### Choose whether it is more appropriate to present the data as a table or a figure: 

        ### As a table:
        df_to_latex(
            df_tag, 'df_tag_formatted'
            caption="<choose a caption suitable for a table in a scientific paper>", 
            note="<If needed, add a note to provide any additional information that is not captured in the caption>",
            glossary=glossary)

        ### As a figure:
        df_to_figure(
            df_tag, 'df_tag_formatted',
            caption="<one line heading of the figure (this will get bolded in the scientific papers).>", 
            note="<If needed, add a note with additional information that will appear below the caption.
                  Do not repeat the caption. Do not repeat the glossary. 
                  Do not specify '** < 0.001' (will add automatically)>",
            glossary=glossary,
            kind='bar',
            y='Coefficient',
            y_ci='CI',  # a column with (lower, upper) tuple values.
            y_p_value='PV',  # a column with p-values.
        )


        ## Process df_next_tag:
        ### etc, for each 'df_*.pkl'
        ```

        Avoid the following:
        Do not provide a sketch or pseudocode; write a complete runnable code including all '# HEADERS' sections.
        Do not explicitly create any graphics or tables; use the provided functions.
        Do not send any presumed output examples.
        ''')

    code_review_prompts: Collection[CodeReviewPrompt] = ()

    def __post_init__(self):
        super().__post_init__()
        self.headers_required_in_code += tuple(f'## {file_name.split(".")[0]}'
                                               for file_name in self.products.get_created_dfs())

    def _get_additional_contexts(self) -> Optional[Dict[str, Any]]:
        return create_pandas_and_stats_contexts(allow_dataframes_to_change_existing_series=True,
                                                enforce_saving_altered_dataframes=False) | {
            'CustomPreventMethods': PreventCalling(
                modules_and_functions=(
                    ('pandas', 'to_numeric', False),
                )
            ),
            'CustomPreventAssignmentToAtt': DataframePreventAssignmentToAttrs(
                forbidden_set_attrs=['columns', 'index'],
            ),
            'PValueMessage': AttrReplacer(
                obj_import_str=PValue, attr='error_message_on_forbidden_func',
                wrapper="Calling `{func_name}` on a PValue object is forbidden."
            ),
        }
