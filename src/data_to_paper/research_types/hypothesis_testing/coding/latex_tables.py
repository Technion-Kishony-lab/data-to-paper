from dataclasses import dataclass
from functools import partial
from typing import Iterable, Any, Type, Tuple, Optional, Dict, Collection

from data_to_paper.base_steps import DebuggerConverser, CheckLatexCompilation
from data_to_paper.base_steps.request_code import CodeReviewPrompt
from data_to_paper.code_and_output_files.code_and_output import CodeAndOutput
from data_to_paper.code_and_output_files.file_view_params import ContentView, ContentViewPurpose, ContentViewParams
from data_to_paper.code_and_output_files.output_file_requirements import TextContentOutputFileRequirement, \
    OutputFileRequirements
from data_to_paper.code_and_output_files.ref_numeric_values import HypertargetFormat, HypertargetPosition
from data_to_paper.code_and_output_files.referencable_text import BaseReferenceableText, convert_str_to_latex_label, \
    NumericReferenceableText
from data_to_paper.latex.tables import get_table_caption
from data_to_paper.research_types.hypothesis_testing.cast import ScientificAgent
from data_to_paper.research_types.hypothesis_testing.coding.base_code_conversers import BaseCreateTablesCodeProductsGPT
from data_to_paper.research_types.hypothesis_testing.coding.original_utils.to_latex_with_note import \
    get_html_from_latex_table, get_latex_table_without_html_comment
from data_to_paper.research_types.hypothesis_testing.coding.utils import get_additional_contexts
from data_to_paper.research_types.hypothesis_testing.coding.utils_modified_for_gpt_use.to_latex_with_note import \
    TABLE_COMMENT_HEADER
from data_to_paper.research_types.hypothesis_testing.coding.utils_modified_for_gpt_use.to_pickle import \
    get_read_pickle_attr_replacer
from data_to_paper.research_types.hypothesis_testing.scientific_products import HypertargetPrefix
from data_to_paper.research_types.hypothesis_testing.coding.latex_table_debugger import LatexTablesDebuggerConverser
from data_to_paper.run_gpt_code.overrides.attr_replacers import PreventAssignmentToAttrs, PreventCalling, AttrReplacer
from data_to_paper.run_gpt_code.overrides.pvalue import PValue, OnStr
from data_to_paper.run_gpt_code.run_contexts import ProvideData
from data_to_paper.run_gpt_code.run_issues import RunIssue, CodeProblem
from data_to_paper.utils import dedent_triple_quote_str


@dataclass
class CreateLatexTablesCodeAndOutput(CodeAndOutput):
    def get_code_header_for_file(self, filename: str) -> Optional[str]:
        # 'table_*.tex' -> '# TABLE *'
        if filename.startswith('table_') and filename.endswith('.tex'):
            return f'# TABLE {filename[6:-4]}'
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
class TableNumericReferenceableText(NumericReferenceableText):
    def _wrap_as_block(self, content: str):
        return f'"{self.filename}":\n```html\n{content}\n```\n'


@dataclass(frozen=True)
class TexTableContentOutputFileRequirement(TextContentOutputFileRequirement):
    filename: str = '*.tex'

    def get_referencable_text(self, content: Any, filename: str = None, num_file: int = 0,
                              content_view: ContentView = None) -> BaseReferenceableText:
        if content_view == ContentViewPurpose.APP_HTML:
            content = get_html_from_latex_table(content)
            result = TableNumericReferenceableText(
                    text=content,
                    filename=filename,
                    hypertarget_prefix=self.hypertarget_prefixes[num_file] if self.hypertarget_prefixes else None,
                    content_view_purpose_converter=self.content_view_purpose_converter,
                )
        else:
            content = get_latex_table_without_html_comment(content)
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
class CreateLatexTablesCodeProductsGPT(BaseCreateTablesCodeProductsGPT, CheckLatexCompilation):
    code_step: str = 'data_to_latex'
    tolerance_for_too_wide_in_pts: Optional[float] = 25.
    debugger_cls: Type[DebuggerConverser] = LatexTablesDebuggerConverser
    code_and_output_cls: Type[CodeAndOutput] = CreateLatexTablesCodeAndOutput
    headers_required_in_code: Tuple[str, ...] = (
        '# IMPORT',
        '# PREPARATION FOR ALL TABLES',
    )
    phrases_required_in_code: Tuple[str, ...] = \
        ('\nfrom my_utils import to_latex_with_note, is_str_in_df, split_mapping, AbbrToNameDef', )
    attrs_to_send_to_debugger: Tuple[str, ...] = \
        BaseCreateTablesCodeProductsGPT.attrs_to_send_to_debugger + ('phrases_required_in_code',)
    user_agent: ScientificAgent = ScientificAgent.InterpretationReviewer
    background_product_fields: Tuple[str, ...] = \
        ('data_file_descriptions', 'research_goal', 'codes:data_preprocessing', 'codes:data_analysis',
         'created_files_content:data_analysis:table_?.pkl')
    allow_data_files_from_sections: Tuple[Optional[str]] = ('data_analysis', )
    supported_packages: Tuple[str, ...] = ('pandas', 'numpy', 'my_utils')
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

    mission_prompt: str = dedent_triple_quote_str('''
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

    code_review_prompts: Collection[CodeReviewPrompt] = ()

    @property
    def first_table_number(self):
        k = len('table_')
        return self.products.get_created_df_tables()[0][k]

    def __post_init__(self):
        super().__post_init__()
        k = len('table_')
        self.headers_required_in_code += tuple(f'# TABLE {file_name[k]}'
                                               for file_name in self.products.get_created_df_tables())

    def _get_additional_contexts(self) -> Optional[Dict[str, Any]]:
        return get_additional_contexts(
            allow_dataframes_to_change_existing_series=True,
            enforce_saving_altered_dataframes=False) | {
            'CustomPreventMethods': PreventCalling(
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
            ),
            'ProvideData': ProvideData(
                data={'compile_to_pdf_func': partial(self._get_static_latex_compilation_func(), is_table=True)}
            ),
        }
