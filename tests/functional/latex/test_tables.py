import os
import pandas as pd
import pytest
from pytest import fixture

from data_to_paper.latex.latex_doc import LatexDocument
from data_to_paper.research_types.hypothesis_testing.coding.original_utils import df_to_latex
from data_to_paper.research_types.hypothesis_testing.coding. \
    utils_modified_for_gpt_use.abbreviations import is_unknown_abbreviation

THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))


@fixture()
def df_table():
    return pd.DataFrame({
        'a': [1, 2, 3],
        'b': [4, 5, 6],
    })


def test_df_to_latex(df_table):
    latex = df_to_latex(df_table, None, caption='test caption', label='table:test', note='this is a note',
                        glossary={'CV': 'coefficient of variation', 'SD': 'standard deviation'})
    latex = latex.replace('@@<', '').replace('>@@', '')
    width = LatexDocument().compile_table(latex, file_stem='test')
    assert 0.1 < width < 0.2


def test_table_with_list():
    df = pd.DataFrame({
        'a': [[1, 2.3578523523523, 3], [4, 5, 6]],
    })
    assert '2.358, ' in df_to_latex(df, None, caption='test caption', label='table:test', note='this is a note')


@pytest.mark.parametrize('phrase, expected', [
    ('Avg.', False),
    ('Fpt.', True),
    ('MyParam', True),
    ('SoP', True),
    ('Avg. Education', False),
    ('Avg. Age', False),
    ('Coef.', False),
    ('Diabetes (0=No, 1=Yes)', False),
    ('7', False),
    ('D', True),
    ('SD', False),
])
def test_is_unknown_abbreviation(phrase, expected):
    assert is_unknown_abbreviation(phrase) == expected
