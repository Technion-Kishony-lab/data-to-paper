
# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping
from typing import Any, Dict, Optional, Tuple

AbbrToNameDef = Dict[Any, Tuple[Optional[str], Optional[str]]]

# PREPARATION FOR ALL TABLES

shared_mapping: AbbrToNameDef = {
    'sex': ('Sex', '0: Female, 1: Male'),
    'age_c': ('Age', 'Age in years, rounded to the nearest half-year'),
    'ht': ('Height', 'Height in centimeters (cm)'),
    'wt': ('Weight', 'Weight in kilograms (kg)'),
    'mean': ('Mean', None),
    'std': ('Standard Deviation', None),
}

special_mapping: AbbrToNameDef = {
    'tube_depth_G': ('OTTD', 'Optimal Tracheal Tube Depth as determined by Chest X-ray in cm')
}

# TABLE 0

df0 = pd.read_pickle('table_0.pkl')

# RENAMING ROWS AND COLUMNS

mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df0, k)}
mapping |= {k: v for k, v in special_mapping.items() if is_str_in_df(df0, k)}

abbrs_to_names, legend = split_mapping(mapping)
df0 = df0.rename(columns=abbrs_to_names, index=abbrs_to_names)

# SAVE AS LATEX

to_latex_with_note(
    df0, 'table_0.tex',
    caption="Descriptive Statistics of Patient Features and OTTD",
    label='table:descriptive-statistics',
    note="This table provides the mean and standard deviation for each variable.",
    legend=legend
)


# TABLE 1

df1 = pd.read_pickle('table_1.pkl')

# SAVE AS LATEX

to_latex_with_note(
    df1, 'table_1.tex',
    caption="Mean Squared Residuals for Random Forest and Elastic Net",
    label='table:squared-residuals',
    note=None,
    legend=None
)


# TABLE 2

df2 = pd.read_pickle('table_2.pkl')

# FORMAT P-VALUE

df2['p-value'] = df2['p-value'].apply(format_p_value)

# SAVE AS LATEX

to_latex_with_note(
    df2, 'table_2.tex',
    caption="Paired T-Test Results for Mean Squared Residuals",
    label='table:t-test',
    note=None,
    legend=None
)

