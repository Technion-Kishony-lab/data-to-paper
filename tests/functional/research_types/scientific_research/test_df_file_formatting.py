from copy import copy

import pandas as pd
import pytest
from pandas import DataFrame
from pathlib import Path

from data_to_paper.code_and_output_files.file_view_params import ViewPurpose
from data_to_paper.latex.latex_doc import LatexDocument
from data_to_paper.research_types.hypothesis_testing.coding.analysis.coding import \
    DataFramePickleContentOutputFileRequirement
from data_to_paper.research_types.hypothesis_testing.coding.displayitems.coding import \
    TexDisplayitemContentOutputFileRequirement
from data_to_paper.run_gpt_code.overrides.dataframes.df_with_attrs import InfoDataFrameWithSaveObjFuncCall
from data_to_paper.run_gpt_code.overrides.pvalue import PValue
from tests.functional.research_types.scientific_research.utils import simulate_save_load
from data_to_paper.research_types.hypothesis_testing.coding.analysis.my_utils.df_to_figure import analysis_df_to_figure
from data_to_paper.research_types.hypothesis_testing.coding.analysis.my_utils.df_to_latex import analysis_df_to_latex
from data_to_paper.research_types.hypothesis_testing.coding.displayitems.my_utils.df_to_figure import \
    displayitems_df_to_figure
from data_to_paper.research_types.hypothesis_testing.coding.displayitems.my_utils.df_to_latex import \
    displayitems_df_to_latex


@pytest.fixture()
def df_tbl_0():
    return pd.DataFrame({
        'coef': [0.1, 0.205, 0.3],
        'CI': [(0.09, 0.11), (0.19123456, 0.21), (0.29, 0.31)],
        'P-value': [PValue(0.001), PValue(2e-8), PValue(0.003)],
    }, index=['app', 'ban', 'ora'])  # apples, bananas, oranges


@pytest.fixture()
def df_with_underscores_in_caption():
    return pd.DataFrame({
        'coefficient': [0.1, 0.205, 0.3],
        'CI': [(0.09, 0.11), (0.19123456, 0.21), (0.29, 0.31)],
        'P-value': [PValue(0.001), PValue(2e-8), PValue(0.003)],
    }, index=['bananas_potatoes', 'bananas_tomatoes', 'bananas_tornadoes'])


def _simulate_analysis(df, is_figure=False) -> InfoDataFrameWithSaveObjFuncCall:
    if is_figure:
        return simulate_save_load(
            analysis_df_to_figure, df, 'df_tbl',
            kind='bar', y='coef', y_ci='CI', y_p_value='P-value', caption='caption1')
    else:
        return simulate_save_load(
            analysis_df_to_latex, df, 'df_tbl', caption='caption1')


def _simulate_displayitems(df: DataFrame, is_figure=False) -> InfoDataFrameWithSaveObjFuncCall:
    df.rename(index={'ban': 'bananas', 'app': 'apples', 'ora': 'oranges'}, inplace=True)
    if is_figure:
        return simulate_save_load(
            displayitems_df_to_figure, df, 'df_tbl_formatted',
            kind='bar', y='coef', y_ci='CI', y_p_value='P-value', caption='caption2', glossary={'coef': 'coefficient'})
    else:
        return simulate_save_load(
            displayitems_df_to_latex, df, 'df_tbl_formatted',
            caption='caption2', glossary={'coef': 'coefficient'})


def _simulate_df_to_latex_analysis_and_displayitems(
        df, is_figure=False) -> (InfoDataFrameWithSaveObjFuncCall, InfoDataFrameWithSaveObjFuncCall):
    df_tbl_1 = _simulate_analysis(df, is_figure)
    df_tbl_2 = _simulate_displayitems(copy(df_tbl_1), is_figure)
    return df_tbl_1, df_tbl_2


@pytest.mark.parametrize('is_figure, expected_func, expected_kwargs', [
    (False, 'df_to_latex', {'caption': 'caption1'}),
    (True, 'df_to_figure', {'caption': 'caption1', 'kind': 'bar', 'y': 'coef', 'y_ci': 'CI', 'y_p_value': 'P-value'}),
])
def test_info_of_df_to_latex_analysis(df_tbl_0, is_figure, expected_func, expected_kwargs):
    df_tbl_1 = _simulate_analysis(df_tbl_0, is_figure)
    assert isinstance(df_tbl_1, InfoDataFrameWithSaveObjFuncCall)
    assert df_tbl_0.equals(df_tbl_1)
    func_call = df_tbl_1.get_func_call()
    func_name, df, label, kwargs = func_call.func_name, func_call.obj, func_call.filename, func_call.kwargs
    assert func_name == expected_func
    assert df.equals(df_tbl_0)
    assert label == 'df_tbl'
    assert kwargs == expected_kwargs


@pytest.mark.parametrize('is_figure, expected_func, expected_kwargs', [
    (False, 'df_to_latex', {'caption': 'caption2', 'glossary': {'coef': 'coefficient'}}),
    (True, 'df_to_figure', {'caption': 'caption2', 'kind': 'bar', 'y': 'coef', 'y_ci': 'CI', 'y_p_value': 'P-value',
                            'glossary': {'coef': 'coefficient'}}),
])
def test_info_of_df_to_latex_displayitem(df_tbl_0, is_figure, expected_func, expected_kwargs):
    df_tbl_1, df_tbl_2 = _simulate_df_to_latex_analysis_and_displayitems(df_tbl_0, is_figure)

    assert isinstance(df_tbl_2, InfoDataFrameWithSaveObjFuncCall)
    assert df_tbl_0.values.tolist() == df_tbl_2.values.tolist()
    func_call = df_tbl_2.get_func_call()

    assert func_call.func_name == expected_func
    assert func_call.obj.values.tolist() == df_tbl_1.values.tolist()
    assert func_call.filename == 'df_tbl_formatted'
    assert func_call.kwargs == expected_kwargs


def _check_df_to_str(df, requirement, view_purpose, expected):
    if not isinstance(expected, list):
        with pytest.raises(expected):
            requirement.get_pretty_content_with_header(content=df, filename='df_tbl_1.pkl',
                                                       num_file=2, view_purpose=view_purpose)
        print('Properly raised')
    else:
        s = requirement.get_pretty_content_with_header(content=df, filename='df_tbl_1.pkl',
                                                       num_file=2, view_purpose=view_purpose)
        print(s)
        for expected_line in expected:
            assert expected_line in s
        return s


@pytest.mark.parametrize('is_figure, view_purpose, expected', [
    (False, ViewPurpose.CODE_REVIEW, ['### df_tbl_1.pkl', '```output\n', '"ban",0.205,(0.1912, 0.21),2e-08']),
    (False, ViewPurpose.PRODUCT, ['### df_tbl_1.pkl', '```output\n', '"ban",0.205,(0.1912, 0.21),<1e-06']),
    # (False, ViewPurpose.HYPERTARGET_PRODUCT, ValueError),
    (False, ViewPurpose.APP_HTML, ['<h3>df_tbl_1.pkl</h3>', '<td>2e-08</td>']),
    (False, ViewPurpose.FINAL_APPENDIX, ['ban 0.205  (0.1912, 0.21)   2e-08']),
    # (False, ViewPurpose.FINAL_INLINE, ValueError),
    (True, ViewPurpose.CODE_REVIEW, ['"ban",0.205,(0.1912, 0.21),2e-08']),
    (True, ViewPurpose.PRODUCT, ['"ban",0.205,(0.1912, 0.21),<1e-06']),
    # (True, ViewPurpose.HYPERTARGET_PRODUCT, ValueError),
    (True, ViewPurpose.APP_HTML, ['<th>ban</th>', '<td>2e-08</td>', "df.plot(kind='bar', y='coef')"]),
    (True, ViewPurpose.FINAL_APPENDIX, ['ban 0.205  (0.1912, 0.21)   2e-08']),
    # (True, ViewPurpose.FINAL_INLINE, ValueError),
])
def test_view_df_to_latex_analysis(df_tbl_0, is_figure, view_purpose, expected):
    print('\n')
    print(is_figure, view_purpose)
    df_tbl_1, df_tbl_2 = _simulate_df_to_latex_analysis_and_displayitems(df_tbl_0, is_figure)
    requirement = DataFramePickleContentOutputFileRequirement('df_*.pkl')
    _check_df_to_str(df_tbl_1, requirement, view_purpose, expected)


@pytest.mark.parametrize('is_figure, view_purpose, expected', [
    (False, ViewPurpose.CODE_REVIEW,
     [r'\caption{caption2}', r'\item \textbf{coef}: coefficient',
      r'\textbf{bananas} & 0.205 & (0.1912, 0.21) & $<$1e-06 \\', '```latex\n']),
    (False, ViewPurpose.PRODUCT,
     [r'\caption{caption2}', r'\item \textbf{coef}: coefficient',
      r'\textbf{bananas} & 0.205 & (0.1912, 0.21) & $<$1e-06 \\', '```latex\n']),
    (False, ViewPurpose.HYPERTARGET_PRODUCT,
     [r'\caption{caption2}', r'\item \textbf{coef}: coefficient',
      r'\textbf{bananas} & \hypertarget{C1a}{0.205} & (\hypertarget{C1b}{0.1912}, '
      r'\hypertarget{C1c}{0.21}) & $<$\hypertarget{C1d}{1e-06} \\',
      '```latex\n']),
    (False, ViewPurpose.APP_HTML,
     ['<h3>df_tbl_1.pkl</h3>', '<b>caption2</b>', '&lt;1e-06']),
    (False, ViewPurpose.FINAL_APPENDIX,
     [r'\textbf{bananas} & 0.205 & (0.1912, 0.21) & $<$1e-06 \\']),
    (False, ViewPurpose.FINAL_INLINE,
     [r'\item \textbf{coef}: coefficient', r'$<$\raisebox{2ex}{\hypertarget{C1d}{}}1e-06']),
    (True, ViewPurpose.CODE_REVIEW, []),
    (True, ViewPurpose.PRODUCT,
     [r'% "bananas",0.205,(0.1912, 0.21),<1e-06', r'\label{figure:df-tbl-formatted}',
      r"% P-values for y-values were taken from column: 'P-value'."]),
    (True, ViewPurpose.HYPERTARGET_PRODUCT,
     ["```latex\n", r"\begin{figure}",
      "{df_tbl_formatted.png}", "% df.plot(kind='bar', y='coef')",
      r'% "bananas",\hypertarget{C1a}{0.205},(\hypertarget{C1b}{0.1912}, '
      r'\hypertarget{C1c}{0.21}),<\hypertarget{C1d}{1e-06}']),
    (True, ViewPurpose.APP_HTML,
     ['* p &lt; 0.01', '<td>&lt;1e-06</td>']),
    (True, ViewPurpose.FINAL_APPENDIX,
     [r"<(*@\raisebox{2ex}{\hypertarget{C1d}{}}@*)1e-06"]),
    (True, ViewPurpose.FINAL_INLINE,
     [r'\label{figure:df-tbl-formatted}',
      r'% "bananas",0.205,(0.1912, 0.21),<1e-06',
      'ns p $>$= 0.01', '% "bananas",0.205,(0.1912, 0.21),<1e-06',
      "% df.plot(kind='bar', y='coef')"]),
])
def test_view_df_to_latex_displayitems(df_tbl_0, is_figure, view_purpose, expected):
    print('\n')
    print(is_figure, view_purpose)
    df_tbl_1, df_tbl_2 = _simulate_df_to_latex_analysis_and_displayitems(df_tbl_0, is_figure)
    requirement = TexDisplayitemContentOutputFileRequirement('df_*.pkl')
    _check_df_to_str(df_tbl_2, requirement, view_purpose, expected)


PDF_FOLDER = Path(__file__).parent / 'pdfs'


def test_view_df_to_latex_displayitems_with_underscores_in_caption(df_with_underscores_in_caption):
    print('\n')
    print('df_with_underscores_in_caption', ViewPurpose.FINAL_INLINE)
    df_tbl_1, df_tbl_2 = _simulate_df_to_latex_analysis_and_displayitems(df_with_underscores_in_caption)
    requirement = TexDisplayitemContentOutputFileRequirement('df_*.pkl')
    expected = [r'\textbf{bananas\_potatoes}']
    latex = _check_df_to_str(df_tbl_2, requirement, ViewPurpose.FINAL_INLINE, expected)

    # output_directory = PDF_FOLDER  # To get the pdf file
    output_directory = None  # Just test compilation. Do not save the pdf.
    LatexDocument().compile_table(latex, output_directory=output_directory, file_stem='df_tbl_formatted')
