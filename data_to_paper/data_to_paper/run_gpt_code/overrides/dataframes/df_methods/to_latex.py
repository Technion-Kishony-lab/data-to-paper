from pandas import MultiIndex
from pandas.core.frame import DataFrame
from data_to_paper.latex.clean_latex import replace_special_latex_chars


def carefully_replace_special_latex_chars(s: str) -> str:
    if isinstance(s, str):
        return replace_special_latex_chars(s)
    return s


LATEX_DEFAULT_KWARGS = dict(
    escape=False,
    multicolumn=True,
    multirow=True,
    bold_rows=True,
)


def _escape_strings_in_index(index):
    if isinstance(index, MultiIndex):
        for level in range(len(index.levels)):
            index = index.set_levels(index.levels[level].map(carefully_replace_special_latex_chars), level=level)
            index.names = type(index.names)([carefully_replace_special_latex_chars(name) for name in index.names])
    index = index.map(carefully_replace_special_latex_chars)
    index.name = carefully_replace_special_latex_chars(index.name)
    return index


def _escape_string_in_dataframe(df: DataFrame) -> DataFrame:
    """
    Escape strings in a dataframe so that they can be used in latex.
    Also replace strings in the column names and index.
    use replace_special_latex_chars
    """
    for col_index in range(len(df.columns)):
        if df.iloc[:, col_index].dtype == object:
            df.iloc[:, col_index] = df.iloc[:, col_index].apply(carefully_replace_special_latex_chars)
    df.index = _escape_strings_in_index(df.index)
    df.columns = _escape_strings_in_index(df.columns)
    return df


def to_latex_with_escape(self, *args, original_method=None, on_change=None, **kwargs):
    kwargs = {**LATEX_DEFAULT_KWARGS, **kwargs}
    df = _escape_string_in_dataframe(self.copy())
    caption = kwargs.pop('caption', None)
    if caption is not None:
        caption = carefully_replace_special_latex_chars(caption)
    result = original_method(df, *args, caption=caption, **kwargs)
    return result
