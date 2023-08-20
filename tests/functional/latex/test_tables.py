import os
import pandas as pd
import pytest
from _pytest.fixtures import fixture

from data_to_paper.latex.latex_doc import LatexDocument
from data_to_paper.researches_types.scientific_research.utils_for_gpt_code.original_utils import to_latex_with_note
from data_to_paper.researches_types.scientific_research.utils_for_gpt_code.utils_modified_for_gpt_use.to_latex_with_note import \
    is_unknown_abbreviation

THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))


@fixture()
def df_table():
    return pd.DataFrame({
        'a': [1, 2, 3],
        'b': [4, 5, 6],
    })


def test_to_latex_with_note(df_table):
    latex = to_latex_with_note(df_table, None, note='this is a note', caption='test caption', label='table:test',
                               legend={'CV': 'coefficient of variation', 'SD': 'standard deviation'})
    width = LatexDocument().compile_table(latex, file_stem='test')
    assert 0.1 < width < 0.2


@pytest.mark.parametrize('phrase, expected', [
    ('Avg.', False),
    ('Fpt.', True),
    ('MyParam', True),
    ('SoP', True),
    ('Avg. Education', False),
    ('Avg. Age', False),
    ('Coef.', False),
])
def test_is_unknown_abbreviation(phrase, expected):
    assert is_unknown_abbreviation(phrase) == expected
