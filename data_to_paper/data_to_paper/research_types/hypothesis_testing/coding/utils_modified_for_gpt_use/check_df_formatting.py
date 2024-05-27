import re
from typing import List, Optional, Tuple

import pandas as pd

from data_to_paper.research_types.hypothesis_testing.coding.utils_modified_for_gpt_use.abbreviations import \
    is_unknown_abbreviation
from data_to_paper.run_gpt_code.overrides.pvalue import is_containing_p_value
from data_to_paper.run_gpt_code.run_issues import RunIssue, CodeProblem
from data_to_paper.utils import dedent_triple_quote_str
from data_to_paper.utils.dataframe import extract_df_row_labels, extract_df_column_labels, extract_df_axes_labels


DISPLAYITEMS_TO_FUNC_NAMES = {
    'table': 'to_latex_with_note',
    'figure': 'to_figure_with_note'
}


def _get_creating_func(displayitem: str) -> str:
    return DISPLAYITEMS_TO_FUNC_NAMES[displayitem]


def check_that_index_is_true(df: pd.DataFrame, filename: str, index: bool) -> List[RunIssue]:
    issues = []
    if not index:
        index_is_range = [ind for ind in df.index] == list(range(df.shape[0]))
        if index_is_range:
            msg = 'Your current df index is just a numeric range range, so you will have to re-specify the index. ' \
                  'If there is a column that should be the index, use `df.set_index(...)` to set it as the index.'
        else:
            msg = ''
        issues.append(RunIssue.from_current_tb(
            category='Calling to_latex_with_note',
            code_problem=CodeProblem.OutputFileDesignLevelA,
            item=filename,
            issue=f'Do not call `to_latex_with_note` with `index=False`. '
                  f'I want to be able to extract the row labels from the index.',
            instructions=dedent_triple_quote_str("""
                Please revise the code making sure all tables are created with `index=True`, and that the index is \t
                meaningful.
                """) + msg,
        ))
    return issues


def check_for_repetitive_value_in_column(df: pd.DataFrame, filename: str, displayitem: str = 'table') -> List[RunIssue]:
    issues = []
    for icol in range(df.shape[1]):
        column_label = df.columns[icol]
        data = df.iloc[:, icol]
        if is_containing_p_value(data):
            continue
        try:
            data_unique = data.unique()
        except Exception:
            data_unique = None
        if data_unique is not None and len(data_unique) == 1 and len(data) > 5:
            data0 = data.iloc[0]
            # check if the value is a number
            if not isinstance(data0, (int, float)):
                pass
            elif round(data0) == data0 and data0 < 10:
                pass
            else:
                issues.append(RunIssue(
                    category='Checking df: Repetitive values',
                    code_problem=CodeProblem.OutputFileContentLevelA,
                    item=filename,
                    issue=f'The column "{column_label}" has the same unique value for all rows.',
                    instructions=dedent_triple_quote_str(f"""
                        Please revise the code so that it:
                        * Finds the unique values (use `{column_label}_unique = df["{column_label}"].unique()`)
                        * Asserts that there is only one value. (use `assert len({column_label}_unique) == 1`)
                        * Drops the column from the df (use `df.drop(columns=["{column_label}"])`)
                        * Adds the unique value, {column_label}_unique[0], \t
                        in the {displayitem} note \t
                        (use `note=` in the function `{_get_creating_func(displayitem)}`).

                        There is no need to add corresponding comments to the code. 
                        """),
                ))
    return issues


def checks_that_rows_are_labelled(df: pd.DataFrame, filename: str, index: bool, displayitem: str = 'table'
                                  ) -> List[RunIssue]:
    columns = df.columns
    if index is False and df.shape[0] > 1 and df[columns[0]].dtype != 'object':
        if displayitem == 'table':
            instructions = 'Use `index=True` in the function `to_latex_with_note`.'
        else:
            instructions = 'Use `use_index=True` in the function `to_figure_with_note`.'
        return [RunIssue(
            category='Checking df: Unlabelled rows',
            code_problem=CodeProblem.OutputFileDesignLevelA,
            item=filename,
            issue=f'The df has more than one row, but the rows are not labeled.',
            instructions=dedent_triple_quote_str(f"""
                Please revise the code making sure all tables are created with labeled rows.
                {instructions}
                """),
        )]
    return []


UNALLOWED_CHARS = [
    ('_', 'underscore'),
    ('^', 'caret'),
    ('{', 'curly brace'),
    ('}', 'curly brace')
]


def check_for_unallowed_characters(df: pd.DataFrame, filename: str) -> List[RunIssue]:
    issues = []
    for char, char_name in UNALLOWED_CHARS:
        for is_row in [True, False]:
            if is_row:
                labels = extract_df_row_labels(df, with_title=True, string_only=True)
                index_or_column = 'index'
            else:
                labels = extract_df_column_labels(df, with_title=True, string_only=True)
                index_or_column = 'column'
            unallowed_labels = sorted([label for label in labels if char in label])
            if unallowed_labels:
                issues.append(RunIssue(
                    category=f'The df row/column labels contain un-allowed characters',
                    code_problem=CodeProblem.OutputFileDesignLevelB,
                    issue=dedent_triple_quote_str(f"""
                        The {filename} has {index_or_column} labels containing \t
                        the character "{char}" ({char_name}), which is not allowed.
                        Here are the problematic {index_or_column} labels:
                        {unallowed_labels}
                        """),
                    instructions=dedent_triple_quote_str(f"""
                        Please revise the code to map these {index_or_column} labels to new names \t
                        that do not contain the "{char}" characters.
                        
                        Doublecheck to make sure your code uses `df.rename({index_or_column}=...)` \t
                        with the `{index_or_column}` argument set to a dictionary mapping the old \t
                        {index_or_column} names to the new ones.
                        """)
                ))
    return issues


def check_for_un_legend_abbreviations(df: pd.DataFrame, filename: str, legend: dict, is_narrow: bool,
                                      displayitem: str = 'table') -> List[RunIssue]:
    issues = []
    func = _get_creating_func(displayitem)
    axes_labels = extract_df_axes_labels(df, with_title=False, string_only=True)
    abbr_labels = [label for label in axes_labels if is_unknown_abbreviation(label)]

    # For compatability with `mapping = {k: v for k, v in shared_mapping.items() if k in df.columns or k in df.index}`
    # This is not needed as we added is_str_in_df to the gpt code. Disabling this for now.
    # abbr_labels = [label for label in abbr_labels if label in df.columns or label in df.index]

    un_mentioned_abbr_labels = sorted([label for label in abbr_labels if label not in legend])
    if un_mentioned_abbr_labels:
        instructions = dedent_triple_quote_str(f"""
            Please revise the code making sure all abbreviated labels (of both column and rows!) are explained \t
            in the legend.
            Add the missing abbreviations and their explanations as keys and values in the `legend` argument of the \t
            function `{func}`.
            """)
        if is_narrow:
            instructions += dedent_triple_quote_str(f"""
                Alternatively, since the {displayitem} is not too wide, you can also replace the abbreviated labels with \t
                their full names in the dataframe itself.
                """)
        if legend:
            issue = dedent_triple_quote_str(f"""
                The `legend` argument of `{func}` includes only the following keys:
                {list(legend.keys())}
                We need to add also the following abbreviated row/column labels:
                {un_mentioned_abbr_labels}
                """)
        else:
            issue = dedent_triple_quote_str(f"""
                The {displayitem} needs a legend explaining the following abbreviated labels:
                {un_mentioned_abbr_labels}
                """)
        issues.append(RunIssue(
            category='Displayitem legend',
            code_problem=CodeProblem.OutputFileDesignLevelB,
            item=filename,
            issue=issue,
            instructions=instructions,
        ))
    return issues


def check_legend_does_not_include_labels_that_are_not_in_df(df: pd.DataFrame, filename: str, legend: dict,
                                                            displayitem: str = 'table') -> List[RunIssue]:
    issues = []
    if legend:
        all_labels = extract_df_axes_labels(df, with_title=True, string_only=True)
        un_mentioned_labels = [label for label in legend if label not in all_labels]
        if un_mentioned_labels:
            issues.append(RunIssue(
                category='Displayitem legend',
                code_problem=CodeProblem.OutputFileDesignLevelB,
                item=filename,
                issue=f'The legend of the {displayitem} includes the following labels that are not in the df:\n'
                      f'{un_mentioned_labels}\n'
                      f'Here are the available df row and column labels:\n{all_labels}',
                instructions=dedent_triple_quote_str("""
                    The legend keys should be a subset of the df labels.

                    Please revise the code changing either the legend keys, or the df labels, accordingly.

                    As a reminder: you can also use the `note` argument to add information that is related to the
                    displayitem as a whole, rather than to a specific label.
                    """)
            ))
    return issues


def _create_displayitem_caption_label_issue(filename: str, issue: str) -> RunIssue:
    return RunIssue(
        category='Problem with displayitem caption/label',
        code_problem=CodeProblem.OutputFileDesignLevelB,
        item=filename,
        issue=issue,
        instructions=dedent_triple_quote_str("""
            Please revise the code making sure all displayitems are created with a caption and a label.
            Use the arguments `caption` and `label` of `to_latex_with_note` or `to_figure_with_note`.
            Captions should be suitable for tables/figures of a scientific paper.
            Labels should be in the format `table:<your table label here>`, `figure:<your figure label here>`.
            In addition, you can add:
            - an optional note for further explanations (use the argument `note`)
            - a legend mapping any abbreviated row/column labels to their definitions \t
            (use the argument `legend` argument). 
            """)
    )


def check_displayitem_label(df: pd.DataFrame, filename: str, label: Optional[str],
                            displayitem: str = 'table', prefix: Optional[str] = None) -> List[RunIssue]:
    if prefix is None:
        prefix = displayitem
    if label is None:
        issue = f'The {displayitem} does not have a label.'
    elif not label.startswith(f'{prefix}:'):
        issue = f'The label of the {displayitem} is not in the format `{prefix}:<your label here>`'
    elif ' ' in label:
        issue = f'The label of the {displayitem} should not contain spaces.'
    elif label.endswith(':'):
        issue = f'The label of the {displayitem} should not end with ":"'
    elif label[6:].isnumeric():
        issue = f'The label of the {displayitem} should not be just a number.'
    else:
        return []
    return [_create_displayitem_caption_label_issue(filename, issue)]


def check_displayitem_caption(df: pd.DataFrame, filename: str, text: Optional[str], item_name: str = 'caption',
                              forbidden_starts: Tuple[str] = ('Figure', 'Table'),
                              displayitem: str = 'table') -> List[RunIssue]:
    issues = []
    if text is None:
        issues.append(f'The {displayitem} does not have a {item_name}.')
    else:
        for forbidden_start in forbidden_starts:
            if text.startswith(forbidden_start):
                issues.append(f'The {item_name} of the {displayitem} should not start with "{forbidden_start}".')
        if '...' in text:
            issues.append(f'The {item_name} of the {displayitem} should not contain "..."')
        if re.search(pattern=r'<.*\>', string=text):
            issues.append(f'The {item_name} of the {displayitem} should not contain "<...>"')
    return [_create_displayitem_caption_label_issue(filename, issue) for issue in issues]


def check_note_different_than_caption(df: pd.DataFrame, filename: str, note: Optional[str], caption: Optional[str],
                                      displayitem: str = 'table') -> List[RunIssue]:
    if note is not None and caption is not None and (
            note.lower() in caption.lower() or caption.lower() in note.lower()):
        return [_create_displayitem_caption_label_issue(
            filename,
            issue=f'The note of the {displayitem} should not be the same as the caption.\n'
                  'Notes are meant to provide additional information, not to repeat the caption.')]
    return []
