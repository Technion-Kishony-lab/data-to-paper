
# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
    'age_c': ('AvgAge (yrs)', 'Average age rounded to half years for patients'),
    'ht': ('AvgHt (cm)', 'Average height of patients in cm'),
    'wt': ('AvgWt (kg)', 'Average weight of patients in kg'),
    'tube_depth_G': ('AvgOTTD (cm)', 'Average optimal tracheal tube depth determined by chest X-ray in cm'),
}

# TABLE 0
df = pd.read_pickle('table_0.pkl')
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)}
abbrs_to_names, legend = split_mapping(mapping)
df.rename(columns=abbrs_to_names, index={0: 'Fem.', 1: 'Male'}, inplace=True)

# Save as latex
to_latex_with_note(
    df, 'table_0.tex',
    caption="Statistical analysis of patient data by sex",
    label='table:summary_stats_sex',
    legend=legend
)

# TABLE 1
df = pd.read_pickle('table_1.pkl')
mapping: AbbrToNameDef = {
    'ML Method': ('MLM', 'Machine Learning Methods'),
    'Formula Method': ('FM', 'Formula Methods'),
    'ML MSE': ('SEMlm', 'Squared error of the machine learning model'),
    'Formula MSE': ('SEFm', 'Squared error of the formula based model'),
    't-statistic': ('T-stat', 'Value of T-statistic comparing residuals of ML model and Formula model'),
    'p-value': ('p-val', 'p-value from the T-test comparing residuals of ML model and formula model')
}
abbrs_to_names, legend = split_mapping(mapping)
df['p-value'] = df['p-value'].apply(format_p_value)
df = df.rename(columns=abbrs_to_names, index=lambda x: x.split(' ')[1])

# Save as latex
to_latex_with_note(
    df, 'table_1.tex',
    caption="Comparison of Residual Squared Errors from Machine Learning and Formula-Based Models",
    label='table:comparison_ml_formula',
    legend=legend
)
