from dataclasses import dataclass

import pandas as pd

from data_to_paper.latex.clean_latex import replace_special_latex_chars
from data_to_paper.latex.tables import create_threeparttable
from data_to_paper.utils import dedent_triple_quote_str


@dataclass
class RunUtilsError(Exception):
    message: str

    def __str__(self):
        return self.message


def to_latex_with_note(df: pd.DataFrame, filename: str, *args, note: str = None, **kwargs):
    if not isinstance(df, pd.DataFrame):
        raise ValueError(f'Expected df to be a pandas.DataFrame, got {type(df)}')

    if not isinstance(filename, str):
        raise ValueError(f'Expected filename to be a string, got {type(filename)}')

    if not filename.endswith('.tex'):
        filename = filename + '.tex'

    latex = df.to_latex(*args, **kwargs)

    if note or legend:
        latex = create_threeparttable(latex, note, legend)

    _check_for_errors(latex, df, filename, *args, note=note, **kwargs)

    with open(filename, 'w') as f:
        f.write(latex)


def _check_for_errors(latex: str, df: pd.DataFrame, filename: str, *args, note: str = None, **kwargs):
    caption = kwargs.get('caption', None)
    label = kwargs.get('label', None)
    index = kwargs.get('index', None)
    columns = kwargs.get('columns', None)
    columns = df.columns if columns is None else columns

    if caption is None or label is None:
        missing = 'caption and label' if caption is None and label is None \
            else 'caption' if caption is None else 'label'
        raise RunUtilsError(dedent_triple_quote_str("""
            Note that the table "{filename}" does not have a {missing}.
        
            Please revise the code making sure all tables are created with a caption and a label.
            Use the arguments `caption` and `label` of the function `to_latex_with_note`.
            Captions should be suitable for a table in a scientific paper.
            Labels should be in the format `table:<your table label here>`.
            """).format(filename=filename, missing=missing))

    if not label.startswith('table:'):
        raise RunUtilsError(dedent_triple_quote_str("""
            Note that the label of the table "{filename}" is not in the format `table:<your table label here>`.
            Please revise the code making sure all table labels are in the correct format.
            """).format(filename=filename))

    # Check if the table is a df.describe() table
    description_headers = ('count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max')
    if set(description_headers).issubset(columns) or set(description_headers).issubset(df.index):
        raise RunUtilsError(dedent_triple_quote_str("""
            As per the table "{filename}", \
            note that in scientific tables, it is not customary to include quantiles, or min/max values, \
            especially if the mean and std are also provided.

            Please revise the code so that the table only includes scientifically relevant statistics.
            """).format(filename=filename))

    # Check for repetitive values in a column
    for column_header in columns:
        data = df[column_header]
        if len(data.unique()) == 1 and len(data) > 5:
            data0 = data.iloc[0]
            # check if the value is a number
            if isinstance(data0, (int, float)) and round(data0) == data0 and data0 < 10:
                pass
            else:
                raise RunUtilsError(dedent_triple_quote_str("""
                    Note that the column "{column_header}" of the table "{filename}" has the same unique value \
                    for all rows.
                    
                    Please revise the code so that the table is created without this column, and \
                    the unique value is included instead in the table note \
                    (use the argument `note` of the function `to_latex_with_note`). 
                    """).format(column_header=column_header, filename=filename))

    # Check that the rows are labeled:
    if index is False and df.shape[0] > 1:
        raise RunUtilsError(dedent_triple_quote_str("""
            Note that the rows of the table "{filename}" are not labeled.
            
            Please revise the code making sure all tables are created with labeled rows.
            Use `index=True` in the function `to_latex_with_note`.
            """).format(filename=filename))
