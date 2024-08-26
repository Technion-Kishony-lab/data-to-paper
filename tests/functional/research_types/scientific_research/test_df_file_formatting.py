import pandas as pd
import pytest
from pandas import DataFrame

from data_to_paper.code_and_output_files.file_view_params import ViewPurpose
from data_to_paper.research_types.hypothesis_testing.coding.analysis.coding import \
    DataFramePickleContentOutputFileRequirement
from data_to_paper.research_types.hypothesis_testing.coding.analysis.my_utils import \
    df_to_latex as analysis_df_to_latex
from data_to_paper.research_types.hypothesis_testing.coding.analysis.my_utils import \
    df_to_figure as analysis_df_to_figure
from data_to_paper.research_types.hypothesis_testing.coding.displayitems.coding import \
    TexDisplayitemContentOutputFileRequirement
from data_to_paper.research_types.hypothesis_testing.coding.displayitems.my_utils import \
    df_to_latex as displayitems_df_to_latex
from data_to_paper.research_types.hypothesis_testing.coding.displayitems.my_utils import \
    df_to_figure as displayitems_df_to_figure
from data_to_paper.run_gpt_code.overrides.dataframes.df_with_attrs import ListInfoDataFrame
from data_to_paper.run_gpt_code.overrides.pvalue import PValue
from data_to_paper.run_gpt_code.run_contexts import IssueCollector
from data_to_paper.utils.file_utils import run_in_directory


@pytest.fixture()
def df_tbl_0():
    return pd.DataFrame({
        'coef': [0.1, 0.205, 0.3],
        'CI': [(0.09, 0.11), (0.19123456, 0.21), (0.29, 0.31)],
        'P-value': [PValue(0.001), PValue(2e-8), PValue(0.003)]},
        index=['app', 'ban', 'ora']  # apples, bananas, oranges
    )


def _simulate_analysis(tmpdir, df, is_figure=False):
    with run_in_directory(tmpdir):
        with IssueCollector() as ic:
            if is_figure:
                analysis_df_to_figure(df, 'df_tbl', kind='bar',
                                      y='coef', y_ci='CI', y_p_value='P-value',
                                      caption='caption1')
            else:
                analysis_df_to_latex(df, 'df_tbl', caption='caption1')
        assert ic.issues == []
        return pd.read_pickle('df_tbl.pkl')


def _simulate_displayitems(tmpdir, df: DataFrame, is_figure=False):
    with run_in_directory(tmpdir):
        with IssueCollector() as ic:
            df.rename(index={'ban': 'bananas', 'app': 'apples', 'ora': 'oranges'}, inplace=True)
            if is_figure:
                displayitems_df_to_figure(df, 'df_tbl_formatted', kind='bar',
                                          y='coef', y_ci='CI', y_p_value='P-value',
                                          caption='caption2', glossary={'coef': 'coefficient'})
            else:
                displayitems_df_to_latex(df, 'df_tbl_formatted',
                                         caption='caption2', glossary={'coef': 'coefficient'})
        assert ic.issues == []
        return pd.read_pickle('df_tbl_formatted.pkl')


def _simulate_df_to_latex_analysis_and_displayitems(tmpdir, df, is_figure=False):
    df_tbl_1 = _simulate_analysis(tmpdir, df, is_figure)
    df_tbl_2 = _simulate_displayitems(tmpdir, df_tbl_1, is_figure)
    return df_tbl_1, df_tbl_2


@pytest.mark.parametrize('is_figure, expected_func, expected_kwargs', [
    (False, 'df_to_latex', {'caption': 'caption1'}),
    (True, 'df_to_figure', {'caption': 'caption1', 'kind': 'bar', 'y': 'coef', 'y_ci': 'CI', 'y_p_value': 'P-value'}),
])
def test_info_of_df_to_latex_analysis(tmpdir, df_tbl_0, is_figure, expected_func, expected_kwargs):
    df_tbl_1 = _simulate_analysis(tmpdir, df_tbl_0, is_figure)
    assert isinstance(df_tbl_1, ListInfoDataFrame)
    assert df_tbl_0.equals(df_tbl_1)
    info = df_tbl_1.extra_info
    assert len(info) == 1
    func, df, label, kwargs = info[0]
    assert func == expected_func
    assert df.equals(df_tbl_0)
    assert label == 'df_tbl'
    assert kwargs == expected_kwargs


@pytest.mark.parametrize('is_figure, expected_func, expected_kwargs', [
    (False, 'df_to_latex', {'caption': 'caption2', 'glossary': {'coef': 'coefficient'}}),
    (True, 'df_to_figure', {'caption': 'caption2', 'kind': 'bar', 'y': 'coef', 'y_ci': 'CI', 'y_p_value': 'P-value',
                            'glossary': {'coef': 'coefficient'}}),
])
def test_info_of_df_to_latex_displayitem(tmpdir, df_tbl_0, is_figure, expected_func, expected_kwargs):
    df_tbl_1, df_tbl_2 = _simulate_df_to_latex_analysis_and_displayitems(tmpdir, df_tbl_0, is_figure)

    assert isinstance(df_tbl_2, ListInfoDataFrame)
    assert df_tbl_0.values.tolist() == df_tbl_2.values.tolist()
    info = df_tbl_2.extra_info
    assert len(info) == 2

    func, df, label, kwargs = info[1]
    assert func == expected_func
    assert df.values.tolist() == df_tbl_1.values.tolist()
    assert label == 'df_tbl_formatted'
    assert kwargs == expected_kwargs


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


@pytest.mark.parametrize('is_figure, view_purpose, expected', [
    (False, ViewPurpose.CODE_REVIEW, ['### df_tbl_1.pkl', '```output\n', '"bananas",0.205,(0.1912, 0.21),<1e-06']),
    (False, ViewPurpose.PRODUCT, ['### df_tbl_1.pkl', '```output\n', '"bananas",0.205,(0.1912, 0.21),<1e-06']),
    (False, ViewPurpose.HYPERTARGET_PRODUCT, ValueError),
    (False, ViewPurpose.APP_HTML, ['<h3>df_tbl_1.pkl</h3>', '<td>2e-08</td>']),
    (False, ViewPurpose.FINAL_APPENDIX, ['bananas 0.205  (0.1912, 0.21)   2e-08']),
    (True, ViewPurpose.CODE_REVIEW, []),
    (True, ViewPurpose.PRODUCT, []),
    (True, ViewPurpose.HYPERTARGET_PRODUCT, ValueError),
    (True, ViewPurpose.APP_HTML, []),
    (True, ViewPurpose.FINAL_APPENDIX, []),
])
def test_view_df_to_latex_analysis(tmpdir, df_tbl_0, is_figure, view_purpose, expected):
    print('\n')
    print(is_figure, view_purpose)
    df_tbl_1, df_tbl_2 = _simulate_df_to_latex_analysis_and_displayitems(tmpdir, df_tbl_0, is_figure)
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
     ['<h3>df_tbl_1.pkl</h3>', '<b>caption2</b>', '<td>2e-08</td>']),
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
      "{df_tbl_formatted.png}", "% df.plot(**{'kind': 'bar', 'y': 'coef'})",
      r'% "bananas",\hypertarget{C1a}{0.205},(\hypertarget{C1b}{0.1912}, \hypertarget{C1c}{0.21}),<\hypertarget{C1d}{1e-06}']),
    (True, ViewPurpose.APP_HTML,
     ['* p &lt; 0.01', '<td>&lt;1e-06</td>']),
    (True, ViewPurpose.FINAL_APPENDIX,
     []),
    (True, ViewPurpose.FINAL_INLINE,
     [r'\label{figure:df-tbl-formatted}',
      r'\hypertarget{C0a}{0.1}' + '\n' + r'\hypertarget{C0b}{0.09}',
      'NS p $>$= 0.01', '% "bananas",0.205,(0.1912, 0.21),<1e-06',
      "% df.plot(**{'kind': 'bar', 'y': 'coef'})"]),
])
def test_view_df_to_latex_displayitems(tmpdir, df_tbl_0, is_figure, view_purpose, expected):
    print('\n')
    print(is_figure, view_purpose)
    df_tbl_1, df_tbl_2 = _simulate_df_to_latex_analysis_and_displayitems(tmpdir, df_tbl_0, is_figure)
    requirement = TexDisplayitemContentOutputFileRequirement('df_*.pkl')
    _check_df_to_str(df_tbl_2, requirement, view_purpose, expected)
