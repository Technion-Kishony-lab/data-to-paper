import pandas as pd


def to_latex_with_note(df: pd.DataFrame, filename: str, *args, **kwargs):
    if not isinstance(df, pd.DataFrame):
        raise ValueError(f'Expected df to be a pandas.DataFrame, got {type(df)}')

    if not isinstance(filename, str):
        raise ValueError(f'Expected filename to be a string, got {type(filename)}')

    if not filename.endswith('.tex'):
        filename = filename + '.tex'

    note = kwargs.pop('note', None)
    latex = df.to_latex(*args, **kwargs)
    if note:
        latex = latex.replace(r'\end{tabular}', r'\end{tabular}' + '\n' + r'\begin{minipage}{12cm}' + '\n' +
                              r'\small  ' + note + '\n' + r'\end{minipage}')
    with open(filename, 'w') as f:
        f.write(latex)
