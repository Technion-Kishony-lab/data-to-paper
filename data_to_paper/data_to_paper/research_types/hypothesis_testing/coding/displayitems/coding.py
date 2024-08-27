from dataclasses import dataclass, field
from functools import partial
from typing import Iterable, Any, Type, Tuple, Optional, Dict, Collection, List

from data_to_paper.base_steps import DebuggerConverser, CheckLatexCompilation
from data_to_paper.base_steps.request_code import CodeReviewPrompt
from data_to_paper.code_and_output_files.code_and_output import CodeAndOutput
from data_to_paper.code_and_output_files.file_view_params import ViewPurpose
from data_to_paper.code_and_output_files.output_file_requirements import \
    OutputFileRequirements, DataOutputFileRequirement
from data_to_paper.code_and_output_files.ref_numeric_values import HypertargetFormat, HypertargetPosition
from data_to_paper.research_types.hypothesis_testing.cast import ScientificAgent
from data_to_paper.research_types.hypothesis_testing.coding.base_code_conversers import BaseTableCodeProductsGPT
from data_to_paper.research_types.hypothesis_testing.coding.utils import create_pandas_and_stats_contexts
from data_to_paper.research_types.hypothesis_testing.model_engines import get_model_engine_for_class
from data_to_paper.research_types.hypothesis_testing.scientific_products import HypertargetPrefix, ScientificProducts
from data_to_paper.run_gpt_code.attr_replacers import PreventAssignmentToAttrs, PreventCalling, AttrReplacer
from data_to_paper.run_gpt_code.code_runner import CodeRunner
from data_to_paper.run_gpt_code.overrides.pvalue import PValue, OnStr, OnStrPValue
from data_to_paper.run_gpt_code.run_contexts import ProvideData
from data_to_paper.run_gpt_code.run_issues import RunIssue, CodeProblem
from data_to_paper.servers.model_engine import ModelEngine
from data_to_paper.utils import dedent_triple_quote_str

from .utils import get_df_read_pickle_attr_replacer
from ..analysis.coding import BaseDataFramePickleContentOutputFileRequirement


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
    VIEW_PURPOSE_TO_PVALUE_ON_STR = {
        ViewPurpose.PRODUCT: OnStr.LATEX_SMALLER_THAN,
        ViewPurpose.HYPERTARGET_PRODUCT: OnStr.LATEX_SMALLER_THAN,
        ViewPurpose.APP_HTML: OnStr.WITH_ZERO,
        ViewPurpose.CODE_REVIEW: OnStr.LATEX_SMALLER_THAN,
        ViewPurpose.FINAL_APPENDIX: OnStr.LATEX_SMALLER_THAN,
        ViewPurpose.FINAL_INLINE: OnStr.LATEX_SMALLER_THAN,
    }
    hypertarget_prefixes: Optional[Tuple[str]] = None

    def _is_figure(self, content: Any) -> bool:
        func, args, kwargs = self._get_func_args_kwargs(content)
        return func.__name__ == 'df_to_figure'

    def _get_hyper_target_format(self, content: Any, filename: str = None, num_file: int = 0,
                                 view_purpose: ViewPurpose = None) -> HypertargetFormat:
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

    def _convert_content_to_labeled_text(self, content: Any, filename: str = None, num_file: int = 0,
                                         view_purpose: ViewPurpose = None) -> str:
        func, args, kwargs = self._get_func_args_kwargs(content)
        pvalue_on_str = self._convert_view_purpose_to_pvalue_on_str(view_purpose)
        with OnStrPValue(pvalue_on_str):
            return func(*args, **kwargs, should_format=True)

    def _get_content_and_header_for_final_inline(
            self, content: Any, filename: str = None, num_file: int = 0, level: int = 3,
            view_purpose: ViewPurpose = ViewPurpose.FINAL_INLINE):
        text, header_refs = self.get_formatted_text_and_header_references(content, filename, num_file, view_purpose)
        return text, f'% {filename}\n' + '\n'.join(header_ref.to_str() for header_ref in header_refs)


@dataclass
class UtilsCodeRunner(CodeRunner):
    modified_imports: Tuple[Tuple[str, Optional[str]]] = CodeRunner.modified_imports + (
        ('my_utils', 'data_to_paper.research_types.hypothesis_testing.coding.displayitems.my_utils'),
    )


@dataclass
class DisplayitemsDebuggerConverser(DebuggerConverser):
    products: ScientificProducts = None

    def _get_issues_for_created_output_files(self, code_and_output: CodeAndOutput, contexts) -> List[RunIssue]:
        created_pkl_df_files = self.products.get_created_dfs()
        required_tex_files = [file.replace('.pkl', '.tex') for file in created_pkl_df_files]
        created_tex_files = code_and_output.created_files.get_created_content_files()
        missing_tex_files = set(required_tex_files) - set(created_tex_files)
        if len(missing_tex_files):
            return [RunIssue(
                category='Missing output files',
                issue=f"You did not create a tex file for the following tables: {missing_tex_files}",
                instructions=f"Please create a tex file for each table.",
                code_problem=CodeProblem.OutputFileContentLevelA,
            )]
        return super()._get_issues_for_created_output_files(code_and_output, contexts)


@dataclass
class CreateDisplayitemsCodeProductsGPT(BaseTableCodeProductsGPT, CheckLatexCompilation):
    code_step: str = 'data_to_latex'
    tolerance_for_too_wide_in_pts: Optional[float] = 25.
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
    model_engine: ModelEngine = \
        field(default_factory=lambda: get_model_engine_for_class(CreateDisplayitemsCodeProductsGPT))
    user_agent: ScientificAgent = ScientificAgent.InterpretationReviewer
    background_product_fields: Tuple[str, ...] = \
        ('data_file_descriptions', 'research_goal', 'codes:data_preprocessing', 'codes:data_analysis',
         'created_files_content:data_analysis:df_*.pkl')
    allow_data_files_from_sections: Tuple[Optional[str]] = ('data_analysis', )
    supported_packages: Tuple[str, ...] = ('pandas', 'numpy', 'my_utils')
    output_file_requirements: OutputFileRequirements = OutputFileRequirements([
        TexDisplayitemContentOutputFileRequirement('df_*_formatted.pkl',
                                                   minimal_count=1,
                                                   hypertarget_prefixes=HypertargetPrefix.LATEX_TABLES.value),
        DataOutputFileRequirement('df_*_formatted.png', minimal_count=0, should_make_available_for_next_steps=False)])

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

        For each df_*.pkl file, your code should:

        * Rename column and row names: You should provide a new name to any column or row label that is abbreviated \t
        or technical, or that is otherwise not self-explanatory.

        * Provide glossary definitions: You should provide a full definition for any name (or new name) \t
        in the df that satisfies any of the following: 
        - Remains abbreviated, or not self-explanatory, even after renaming.
        - Is an ordinal/categorical variable that requires clarification of the meaning of each of its possible values.
        - Contains unclear notation, like '*' or ':'
        - Represents a numeric variable that has units, that need to be specified.        

        To avoid re-naming mistakes, you should define for each df a dictionary, \t
        `mapping: AbbrToNameDef`, which maps any original \t
        column and row names that are abbreviated or not self-explanatory to an optional new name, \t
        and an optional definition.
        If different df share several common labels, then you can build a `shared_mapping`, \t
        from which you can extract the relevant labels for each table/figure.

        Overall, the code must have the following structure (### are my instructions, not part of the code):

        ```python
        # IMPORT
        import pandas as pd
        from my_utils import df_to_latex, df_to_figure, is_str_in_df, split_mapping, AbbrToNameDef

        # PREPARATION FOR ALL TABLES AND FIGURES
        ### As applicable, define a shared mapping for labels that are common to all df. For example:
        shared_mapping: AbbrToNameDef = {
            'AvgAge': ('Avg. Age', 'Average age, years'),
            'BT': ('Body Temperature', '1: Normal, 2: High, 3: Very High'),
            'W': ('Weight', 'Participant weight, kg'),
            'MRSA': ('MRSA', 'Infected with Methicillin-resistant Staphylococcus aureus, 1: Yes, 0: No'),
            ...: (..., ...),
        }
        ### This is of course just an example. 
        ### Consult with the "{data_file_descriptions}" and the "{codes:data_analysis}" 
        ### for choosing the actual labels and their proper scientific names and definitions.

        # Process df_tag:  ### tag is a placeholder for the actual name of the df created by the {codes:data_analysis}
        df_tag = pd.read_pickle('df_tag.pkl')

        # Format values:
        ### If not needed, write '# Not Applicable' under the '# Format values:' header.
        ### Rename technical values to scientifically-suitable values. For example:
        df_tag['MRSA'] = df_tag['MRSA'].apply(lambda x: 'Yes' if x == 1 else 'No')

        # Rename rows and columns:
        ### Rename any abbreviated or not self-explanatory df labels to scientifically-suitable names.
        ### Use the `shared_mapping` if applicable. For example:
        mapping = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df_mrsa_age, k)) 
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
            'ReadPickleAttrReplacer': get_df_read_pickle_attr_replacer(),
            'PValueMessage': AttrReplacer(
                obj_import_str=PValue, attr='error_message_on_forbidden_func',
                wrapper="Calling `{func_name}` on a PValue object is forbidden."
            ),
            'ProvideData': ProvideData(
                data={'compile_to_pdf_func': partial(self._get_static_latex_compilation_func(), is_table=True)}
            ),
        }