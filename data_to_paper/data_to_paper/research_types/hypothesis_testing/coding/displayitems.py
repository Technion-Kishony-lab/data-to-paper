from dataclasses import dataclass
from functools import partial
from typing import Iterable, Any, Type, Tuple, Optional, Dict, Collection

from data_to_paper.base_steps import DebuggerConverser, CheckLatexCompilation
from data_to_paper.base_steps.request_code import CodeReviewPrompt
from data_to_paper.code_and_output_files.code_and_output import CodeAndOutput
from data_to_paper.code_and_output_files.file_view_params import ContentView, ContentViewPurpose, ContentViewParams
from data_to_paper.code_and_output_files.output_file_requirements import TextContentOutputFileRequirement, \
    OutputFileRequirements, DataOutputFileRequirement
from data_to_paper.code_and_output_files.ref_numeric_values import HypertargetFormat, HypertargetPosition
from data_to_paper.code_and_output_files.referencable_text import BaseReferenceableText, convert_str_to_latex_label, \
    NumericReferenceableText, LabeledNumericReferenceableText
from data_to_paper.latex.tables import get_displayitem_caption
from data_to_paper.research_types.hypothesis_testing.cast import ScientificAgent
from data_to_paper.research_types.hypothesis_testing.coding.base_code_conversers import BaseCreateTablesCodeProductsGPT
from data_to_paper.research_types.hypothesis_testing.coding.original_utils.add_html_to_latex import \
    get_html_from_latex, get_latex_without_html_comment
from data_to_paper.research_types.hypothesis_testing.coding.utils import get_additional_contexts
from data_to_paper.research_types.hypothesis_testing.coding.utils_modified_for_gpt_use.label_latex_source import \
    extract_source_filename_from_latex_displayitem
from data_to_paper.research_types.hypothesis_testing.coding.utils_modified_for_gpt_use.to_pickle import \
    get_read_pickle_attr_replacer
from data_to_paper.research_types.hypothesis_testing.scientific_products import HypertargetPrefix
from data_to_paper.research_types.hypothesis_testing.coding.displayitems_debugger import LatexTablesDebuggerConverser
from data_to_paper.run_gpt_code.attr_replacers import PreventAssignmentToAttrs, PreventCalling, AttrReplacer
from data_to_paper.run_gpt_code.overrides.pvalue import PValue, OnStr
from data_to_paper.run_gpt_code.run_contexts import ProvideData
from data_to_paper.run_gpt_code.run_issues import RunIssue, CodeProblem
from data_to_paper.utils import dedent_triple_quote_str
from data_to_paper.utils.text_formatting import wrap_text_with_triple_quotes


@dataclass
class CreateLatexDisplayitemsCodeAndOutput(CodeAndOutput):
    def get_code_header_for_file(self, filename: str) -> Optional[str]:
        # 'df_*.tex' -> '# DF *'
        if filename.startswith('df_') and filename.endswith('.tex'):
            return f'# DF {filename[3:-4]}'
        return None


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


@dataclass
class DisplayitemNumericReferenceableText(LabeledNumericReferenceableText):
    def _wrap_as_block(self, content: str):
        return f'"{self.filename}":\n{wrap_text_with_triple_quotes(content, "html")}\n'


@dataclass(frozen=True)
class TexTableContentOutputFileRequirement(TextContentOutputFileRequirement):
    filename: str = '*.tex'
    referenceable_text_cls: type = LabeledNumericReferenceableText

    def get_referencable_text(self, content: Any, filename: str = None, num_file: int = 0,
                              content_view: ContentView = None) -> BaseReferenceableText:
        if content_view == ContentViewPurpose.APP_HTML:
            content = get_html_from_latex(content)
            result = DisplayitemNumericReferenceableText(
                    text=content,
                    filename=filename,
                    hypertarget_prefix=self.hypertarget_prefixes[num_file] if self.hypertarget_prefixes else None,
                    content_view_purpose_converter=self.content_view_purpose_converter,
                )
        else:
            content = get_latex_without_html_comment(content)
            result = super().get_referencable_text(content, filename, num_file, content_view)
        if content_view == ContentViewPurpose.FINAL_INLINE:
            text = result.text
            pickle_filename = extract_source_filename_from_latex_displayitem(text)
            if pickle_filename:
                # we add a hyperlink to the table caption
                pickle_filename = convert_str_to_latex_label(pickle_filename, 'file')
                caption = get_displayitem_caption(text)
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


png_file_requirement = DataOutputFileRequirement('*.png', minimal_count=1)


@dataclass
class CreateLatexTablesCodeProductsGPT(BaseCreateTablesCodeProductsGPT, CheckLatexCompilation):
    code_step: str = 'data_to_latex'
    tolerance_for_too_wide_in_pts: Optional[float] = 25.
    debugger_cls: Type[DebuggerConverser] = LatexTablesDebuggerConverser
    code_and_output_cls: Type[CodeAndOutput] = CreateLatexDisplayitemsCodeAndOutput
    headers_required_in_code: Tuple[str, ...] = (
        '# IMPORT',
        '# PREPARATION FOR ALL TABLES AND FIGURES',
    )
    phrases_required_in_code: Tuple[str, ...] = \
        ('\nfrom my_utils import to_latex_with_note, to_figure_with_note, is_str_in_df, split_mapping, AbbrToNameDef', )
    attrs_to_send_to_debugger: Tuple[str, ...] = \
        BaseCreateTablesCodeProductsGPT.attrs_to_send_to_debugger + ('phrases_required_in_code',)
    user_agent: ScientificAgent = ScientificAgent.InterpretationReviewer
    background_product_fields: Tuple[str, ...] = \
        ('data_file_descriptions', 'research_goal', 'codes:data_preprocessing', 'codes:data_analysis',
         'created_files_content:data_analysis:df_?.pkl')
    allow_data_files_from_sections: Tuple[Optional[str]] = ('data_analysis', )
    supported_packages: Tuple[str, ...] = ('pandas', 'numpy', 'my_utils')
    output_file_requirements: OutputFileRequirements = OutputFileRequirements(
        [tex_file_requirement, png_file_requirement])

    provided_code: str = dedent_triple_quote_str('''
        def to_latex_with_note(df, filename: str, caption: str, label: str,
                               note: str = None, glossary: Dict[str, str] = None, **kwargs):
            """
            Saves a DataFrame as a LaTeX table with optional note and glossary added below the table.

            Parameters:
            - df, filename, caption, label: as in `df.to_latex`.
            - note (optional): Additional note below the table.
            - glossary (optional): Dictionary mapping abbreviations to full names.
            - **kwargs: Additional arguments for `df.to_latex`.
            """

        def to_figure_with_note(df, filename: str, caption: str, label: str,
                                note: str = None, glossary: Dict[str, str] = None, 
                                x: Optional[str] = None, y: Optional[str] = None, kind: str = 'line',
                                use_index: bool = True, 
                                logx: bool = False, logy: bool = False,
                                xerr: str = None, yerr: str = None,
                                x_ci: Union[str, Tuple[str, str]] = None, y_ci: Union[str, Tuple[str, str]] = None,
                                x_p_value: str = None, y_p_value: str = None,
                                ):
            """
            Saves a DataFrame to a LaTeX figure with caption and optional glossary added below the figure.

            Parameters:
            `df`: DataFrame to plot (with column names and index as scientific labels). 
            `filename` (str): name of a .tex file to create (a matching .png file will also be created). 
            `caption` (str): Caption for the figure (can be multi-line).
            `label` (str): Latex label for the figure, 'figure:xxx'. 
            `glossary` (optional, dict): Dictionary mapping abbreviated df col/row labels to full names.
            
            Parameters for df.plot():
            `x` / `y` (optional, str): Column name for x-axis / y-axis values.
            `kind` (str): Type of plot: 'line', 'scatter', 'bar'.
            `use_index` (bool): If True, use the index as x-axis values.
            `logx` / `logy` (bool): If True, use log scale for x/y axis.
            `xerr` / `yerr` (optional, str): Column name for x/y error bars.
            
            Additional plotting options:
            `x_p_value` / `y_p_value` (optional, str): Column name for x/y p-values to plot as stars above the data points.
                p-values are converted to: '***' if < 0.001, '**' if < 0.01, '*' if < 0.05, 'NS' if >= 0.05.

            Instead of xerr/yerr, you can directly provide confidence intervals:
            `x_ci` / `y_ci` (optional, str or (str, str)): an be either a single column name where each row contains
                a 2-element tuple (n x 2 matrix when expanded), or a list containing two column names 
                representing the lower and upper bounds of the confidence interval.
            
            Note on error bars (explanation for y-axis is provided, x-axis is analogous):
            Either `yerr` or `y_ci` can be provided, but not both.
            If `yerr` is provided, the plotted error bars are (df[y]-df[yerr], df[y]+df[yerr]).
            If `y_ci` is provided, the plotted error bars are (df[y_ci][0], df[y_ci][1]).
            Note that unlike yerr, the y_ci are NOT added to the nominal df[y] values. 
            Instead, the provided y_ci values should flank the nominal df[y] values.
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

    mission_prompt: str = dedent_triple_quote_str('''
        Please write a Python code to convert and re-style the "df_?.pkl" dataframes created \t
        by our "{codes:data_analysis}" into latex tables/figures suitable for our scientific paper.

        Your code should use the following 4 custom functions provided for import from `my_utils`: 

        ```python
        {provided_code}
        ```

        Your code should:

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
        from my_utils import to_latex_with_note, to_figure_with_note, is_str_in_df, split_mapping, AbbrToNameDef

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

        # DF {first_df_number}: <short header>
        df{first_df_number} = pd.read_pickle('df_{first_df_number}.pkl')

        # Format values:
        ### If not needed, write '# Not Applicable' under the '# Format values:' header.
        ### Rename technical values to scientifically-suitable values. For example:
        df{first_df_number}['MRSA'] = df{first_df_number}['MRSA'].apply(lambda x: 'Yes' if x == 1 else 'No')

        # Rename rows and columns:
        ### Rename any abbreviated or not self-explanatory df labels to scientifically-suitable names.
        ### Use the `shared_mapping` if applicable. For example:
        mapping{first_df_number} = dict((k, v) for k, v in shared_mapping.items() \t
        if is_str_in_df(df{first_df_number}, k)) 
        mapping{first_df_number} |= {
            'PV': ('P-value', None),
            'CI': ('CI', '95% Confidence Interval'),
            'Sex_Age': ('Age * Sex', 'Interaction term between Age and Sex'),
        }
        abbrs_to_names{first_df_number}, glossary{first_df_number} = split_mapping(mapping{first_df_number})
        df{first_df_number} = df{first_df_number}.rename(columns=abbrs_to_names{first_df_number}, \t
        index=abbrs_to_names{first_df_number})
        
        # <Choose whether it is more appropriate to present the data as a table or a figure.>
        # <Use either `to_latex_with_note` or `to_figure_with_note`> 

        # Creat latex table:
        to_latex_with_note(
            df{first_df_number}, 'df_{first_df_number}.tex',
            caption="<choose a caption suitable for a table in a scientific paper>", 
            label='<table:xxx>',
            note="<If needed, add a note to provide any additional information that is not captured in the caption>",
            glossary=glossary{first_df_number})
        
        # Create latex figure:
        to_figure_with_note(
            df{first_df_number}, 'df_{first_df_number}.tex',
            caption="<one line heading of the figure (this will get bolded in the scientific papers).>", 
            label='<figure:xxx>',
            note="<If needed, add a note with additional information that will appear below the caption.
                  Do not repeat the caption. Do not repeat the glossary. 
                  Do not specify '** < 0.001' (will add automatically)>",
            glossary=glossary{first_df_number},
            kind='bar',
            y='coef',
            y_ci='CI',  # or y_ci=('CI_LB', 'CI_UB')
            y_p_value='PV',  # a column with p-values for the y values. Will be presented as stars in the plot.
        )


        # DF <?>
        ### <etc, all 'df_?.pkl' files>
        ```

        Avoid the following:
        Do not provide a sketch or pseudocode; write a complete runnable code including all '# HEADERS' sections.
        Do not explicitly create any graphics or tables; use the provided functions.
        Do not send any presumed output examples.
        ''')

    code_review_prompts: Collection[CodeReviewPrompt] = ()

    @property
    def first_df_number(self):
        k = len('df_')
        return self.products.get_created_dfs()[0][k]

    def __post_init__(self):
        super().__post_init__()
        k = len('df_')
        self.headers_required_in_code += tuple(f'# DF {file_name[k]}'
                                               for file_name in self.products.get_created_dfs())

    def _get_additional_contexts(self) -> Optional[Dict[str, Any]]:
        return get_additional_contexts(
            allow_dataframes_to_change_existing_series=True,
            enforce_saving_altered_dataframes=False) | {
            'CustomPreventMethods': PreventCalling(
                modules_and_functions=(
                    ('pandas', 'to_numeric', False),
                )
            ),
            'CustomPreventAssignmentToAtt': DataframePreventAssignmentToAttrs(
                forbidden_set_attrs=['columns', 'index'],
            ),
            'ReadPickleAttrReplacer': get_read_pickle_attr_replacer(),
            'PValueMessage': AttrReplacer(
                obj_import_str=PValue, attr='error_message_on_forbidden_func',
                wrapper="Calling `{func_name}` on a PValue object is forbidden."
            ),
            'ProvideData': ProvideData(
                data={'compile_to_pdf_func': partial(self._get_static_latex_compilation_func(), is_table=True)}
            ),
        }
