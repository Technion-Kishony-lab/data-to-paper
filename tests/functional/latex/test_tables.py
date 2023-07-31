import os
import pandas as pd
from _pytest.fixtures import fixture

from data_to_paper.latex.latex_doc import LatexDocument
from data_to_paper.run_gpt_code.run_utils import to_latex_with_note

THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))


@fixture()
def df_table():
    return pd.DataFrame({
        'a': [1, 2, 3],
        'b': [4, 5, 6],
    })


def test_to_latex_with_note(df_table):
    to_latex_with_note(df_table, 'test.tex', note='this is a note', caption='test caption', label='table:test',
                       legend={'CV': 'coefficient of variation', 'SD': 'standard deviation'})
    with open('test.tex', 'r') as f:
        latex = f.read()

    width = LatexDocument().compile_table(latex, file_stem='test')
    assert 0.1 < width < 0.2
