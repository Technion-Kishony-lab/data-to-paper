from functools import partial

from pandas import MultiIndex
from pandas.core.frame import DataFrame
from data_to_paper.latex.clean_latex import replace_special_latex_chars

from data_to_paper.run_gpt_code.overrides.dataframes.utils import format_float

original_to_latex = DataFrame.to_latex


def carefully_replace_special_latex_chars(s: str) -> str:
    if isinstance(s, str):
        return replace_special_latex_chars(s)
    return s


LATEX_DEFAULT_KWARGS = dict(
    float_format=partial(format_float, float_format='.3g'),
    escape=False,
    multicolumn=True,
    multirow=True,
    bold_rows=True,
)


def _escape_string_in_dataframe(df: DataFrame) -> DataFrame:
    """
    Escape strings in a dataframe so that they can be used in latex.
    Also replace strings in the column names and index.
    use replace_special_latex_chars
    """
    for col_index in range(len(df.columns)):
        if df.iloc[:, col_index].dtype == object:
            df.iloc[:, col_index] = df.iloc[:, col_index].apply(carefully_replace_special_latex_chars)
    if isinstance(df.index, MultiIndex):
        for level in range(len(df.index.levels)):
            df.index = df.index.set_levels(df.index.levels[level].map(carefully_replace_special_latex_chars),
                                           level=level)
            df.index.names = type(df.index.names)([carefully_replace_special_latex_chars(name)
                                                   for name in df.index.names])
    df.index = df.index.map(carefully_replace_special_latex_chars)
    df.index.name = carefully_replace_special_latex_chars(df.index.name)
    df.columns = df.columns.map(carefully_replace_special_latex_chars)
    return df


def to_latex(self, *args, **kwargs):
    kwargs = {**LATEX_DEFAULT_KWARGS, **kwargs}
    df = _escape_string_in_dataframe(self.copy())
    caption = kwargs.pop('caption', None)
    if caption is not None:
        caption = carefully_replace_special_latex_chars(caption)
    result = original_to_latex(df, *args, caption=caption, **kwargs)
    return result
