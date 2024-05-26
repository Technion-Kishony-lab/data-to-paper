import re
from typing import List, Optional

import pandas as pd

from data_to_paper.research_types.hypothesis_testing.coding.utils_modified_for_gpt_use.abbreviations import \
    is_unknown_abbreviation
from data_to_paper.run_gpt_code.overrides.pvalue import is_containing_p_value
from data_to_paper.run_gpt_code.run_issues import RunIssue, CodeProblem
from data_to_paper.utils import dedent_triple_quote_str
from data_to_paper.utils.dataframe import extract_df_row_labels, extract_df_column_labels, extract_df_axes_labels


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


def check_for_repetitive_value_in_column(df: pd.DataFrame, filename: str) -> List[RunIssue]:
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
                        * Creates the table without this column (use `df.drop(columns=["{column_label}"])`)
                        * Adds the unique value, {column_label}_unique[0], \t
                        in the table note (use `note=` in the function `to_latex_with_note`).

                        There is no need to add corresponding comments to the code. 
                        """),
                ))
    return issues


def checks_that_rows_are_labelled(df: pd.DataFrame, filename: str, index: bool) -> List[RunIssue]:
    columns = df.columns
    if index is False and df.shape[0] > 1 and df[columns[0]].dtype != 'object':
        return [RunIssue(
            category='Checking df: Unlabelled rows',
            code_problem=CodeProblem.OutputFileDesignLevelA,
            item=filename,
            issue=f'The table has more than one row, but the rows are not labeled.',
            instructions=dedent_triple_quote_str("""
                Please revise the code making sure all tables are created with labeled rows.
                Use `index=True` in the function `to_latex_with_note`.
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
                    category=f'Table row/column labels contain un-allowed characters',
                    code_problem=CodeProblem.OutputFileDesignLevelB,
                    issue=dedent_triple_quote_str(f"""
                        Table {filename} has {index_or_column} labels containing \t
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


def check_for_unexplained_abbreviations(df: pd.DataFrame, filename: str, legend: dict, is_narrow: bool
                                        ) -> List[RunIssue]:
    issues = []
    axes_labels = extract_df_axes_labels(df, with_title=False, string_only=True)
    abbr_labels = [label for label in axes_labels if is_unknown_abbreviation(label)]

    # For compatability with `mapping = {k: v for k, v in shared_mapping.items() if k in df.columns or k in df.index}`
    # This is not needed as we added is_str_in_df to the gpt code. Disabling this for now.
    # abbr_labels = [label for label in abbr_labels if label in df.columns or label in df.index]

    un_mentioned_abbr_labels = sorted([label for label in abbr_labels if label not in legend])
    if un_mentioned_abbr_labels:
        instructions = dedent_triple_quote_str("""
            Please revise the code making sure all abbreviated labels (of both column and rows!) are explained \t
            in their table legend.
            Add the missing abbreviations and their explanations as keys and values in the `legend` argument of the \t
            function `to_latex_with_note`.
            """)
        if is_narrow:
            instructions += dedent_triple_quote_str("""
                Alternatively, since the table is not too wide, you can also replace the abbreviated labels with \t
                their full names in the dataframe itself.
                """)
        if legend:
            issue = dedent_triple_quote_str("""
                The `legend` argument of `to_latex_with_note` includes only the following keys:
                {legend_keys}
                We need to add also the following abbreviated row/column labels:
                {un_mentioned_abbr_labels}
                """).format(legend_keys=list(legend.keys()), un_mentioned_abbr_labels=un_mentioned_abbr_labels)
        else:
            issue = dedent_triple_quote_str("""
                The table needs a legend explaining the following abbreviated labels:
                {un_mentioned_abbr_labels}
                """).format(un_mentioned_abbr_labels=un_mentioned_abbr_labels)
        issues.append(RunIssue(
            category='Table legend',
            code_problem=CodeProblem.OutputFileDesignLevelB,
            item=filename,
            issue=issue,
            instructions=instructions,
        ))
    return issues


def check_legend_does_not_include_labels_that_are_not_in_table(df: pd.DataFrame, filename: str, legend: dict
                                                               ) -> List[RunIssue]:
    issues = []
    if legend:
        all_labels = extract_df_axes_labels(df, with_title=True, string_only=True)
        un_mentioned_labels = [label for label in legend if label not in all_labels]
        if un_mentioned_labels:
            issues.append(RunIssue(
                category='Table legend',
                code_problem=CodeProblem.OutputFileDesignLevelB,
                item=filename,
                issue=f'The legend of the table includes the following labels that are not in the table:\n'
                      f'{un_mentioned_labels}\n'
                      f'Here are the available table row and column labels:\n{all_labels}',
                instructions=dedent_triple_quote_str("""
                    The legend keys should be a subset of the table labels.

                    Please revise the code changing either the legend keys, or the table labels, accordingly.

                    As a reminder: you can also use the `note` argument to add information that is related to the
                    table as a whole, rather than to a specific label.
                    """)
            ))
    return issues


def _create_table_caption_label_issue(filename: str, issue: str) -> RunIssue:
    return RunIssue(
        category='Problem with table caption/label',
        code_problem=CodeProblem.OutputFileDesignLevelB,
        item=filename,
        issue=issue,
        instructions=dedent_triple_quote_str("""
            Please revise the code making sure all tables are created with a caption and a label.
            Use the arguments `caption` and `label` of the function `to_latex_with_note`.
            Captions should be suitable for a table in a scientific paper.
            Labels should be in the format `table:<your table label here>`.
            In addition, you can add:
            - an optional note for further explanations \t
            (use the argument `note` of the function `to_latex_with_note`)
            - a legend mapping any abbreviated row/column labels to their definitions \t
            (use the argument `legend` of the function `to_latex_with_note`) 
            """)
    )


def check_table_label(df: pd.DataFrame, filename: str, label: Optional[str]) -> List[RunIssue]:
    if label is None:
        issue = f'The table does not have a label.'
    elif not label.startswith('table:'):
        issue = 'The label of the table is not in the format `table:<your table label here>`'
    elif ' ' in label:
        issue = 'The label of the table should not contain spaces.'
    elif label.endswith(':'):
        issue = 'The label of the table should not end with ":"'
    elif label[6:].isnumeric():
        issue = 'The label of the table should not be just a number.'
    else:
        return []
    return [_create_table_caption_label_issue(filename, issue)]


def check_table_caption(df: pd.DataFrame, filename: str, text: Optional[str], item_name: str = 'caption'
                        ) -> List[RunIssue]:
    if text is None:
        issue = f'The table does not have a {item_name}.'
    elif text.lower().startswith('table'):
        issue = f'The {item_name} of the table should not start with "Table ..."'
    elif '...' in text:
        issue = f'The {item_name} of the table should not contain "..."'
    elif re.search(pattern=r'<.*\>', string=text):
        issue = f'The {item_name} of the table should not contain "<...>"'
    else:
        return []
    return [_create_table_caption_label_issue(filename, issue)]


def check_note_different_than_caption(df: pd.DataFrame, filename: str, note: Optional[str], caption: Optional[str]
                                      ) -> List[RunIssue]:
    if note is not None and caption is not None and note.lower() == caption.lower():
        return [_create_table_caption_label_issue(
            filename,
            issue='The note of the table should not be the same as the caption.\n'
                  'Notes are meant to provide additional information, not to repeat the caption.'
        )]
    return []
