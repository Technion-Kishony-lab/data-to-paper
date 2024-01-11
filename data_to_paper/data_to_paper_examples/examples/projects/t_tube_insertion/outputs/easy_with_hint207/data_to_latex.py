
# IMPORTS
import pandas as pd
from typing import Dict, Any, Tuple, Optional
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
    'age_c mean': ('Average Age (mean)', 'Average age in years'),
    'age_c std': ('Average Age (std)', 'Standard deviation of age'),
    'ht mean': ('Average Height (mean)', 'Average height in cm'),
    'ht std': ('Average Height (std)', 'Standard deviation of height')
}

# TABLE 0:
df = pd.read_pickle('table_0.pkl')

# TRANPOSE IF REQUIRED
df = df.T

# RENAME ROWS AND COLUMNS
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)}
abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(
 df, 'table_0.tex',
 caption="Descriptive statistics of height and age stratified by sex", 
 label='table:age_height_by_sex',
 note="0: Female, 1: Male",
 legend=legend
)

# TABLE 1:
df = pd.read_pickle('table_1.pkl')

# RENAME ROWS AND COLUMNS
mapping = {
    'mse': ('MSE', 'Mean Squared Error'),
    'Random Forest': ('Random Forest', 'Random Forest Regression model'),
    'ElasticNet': ('ElasticNet', 'ElasticNet Regression model')
}

abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(
 df, 'table_1.tex',
 caption="Performance metrics of the Random Forest and ElasticNet models", 
 label='table:model_performance',
 note=None,
 legend=legend
)

# TABLE 2:
df = pd.read_pickle('table_2.pkl')

# FORMAT VALUES
df['pvalue'] = df['pvalue'].apply(format_p_value)

# RENAME ROWS AND COLUMNS
mapping = {
    'statistic': ('Statistic', 'T-statistic'),
    'pvalue': ('P-value', 'P-value from two-tailed paired t-test'),
    'Comparison': ('Comparison', 'Comparison of residuals')
}

abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(
 df, 'table_2.tex',
 caption="Comparison of residuals of the Random Forest and ElasticNet models", 
 label='table:model_comparison',
 note=None,
 legend=legend
)
