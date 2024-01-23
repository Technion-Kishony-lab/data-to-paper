
# IMPORT
import pandas as pd
from typing import Dict, Any, Tuple, Optional
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
    'RF_model': ('Random Forest MSE', 'Mean Squared Error for Random Forest Model Predictions'),
    'EN_model': ('Elastic Net MSE', 'Mean Squared Error for Elastic Net Model Predictions'),
    'Mean_squared_residuals': ('Mean Squared Residuals', None),
    'Paired_t_test': ('Paired t-test', None)
}

# TABLE 1:
df1 = pd.read_pickle('table_1.pkl')

# RENAME ROWS AND COLUMNS
mapping1 = {k: v for k, v in shared_mapping.items() if is_str_in_df(df1, k)}
abbrs_to_names1, legend1 = split_mapping(mapping1)
df1 = df1.rename(columns=abbrs_to_names1, index=abbrs_to_names1)

# Save as latex:
to_latex_with_note(
 df1, 'table_1.tex',
 caption="Mean Squared Error Comparisons for Machine Learning Models", 
 label='table:model_mse_comparison',
 legend=legend1)

# TABLE 2:
df2 = pd.read_pickle('table_2.pkl')

# FORMAT VALUES 
df2['p_value'] = df2['p_value'].apply(format_p_value)

# RENAME ROWS AND COLUMNS 
mapping2 = {
    't_statistic': ('T-statistic', 'T-statistic for paired t-test comparison of model predictions'),
    'p_value': ('P-value', 'Significance value for paired t-test comparison of model predictions'),
}

mapping2 = {k: v for k, v in shared_mapping.items() if is_str_in_df(df2, k)} | mapping2
abbrs_to_names2, legend2 = split_mapping(mapping2)
df2 = df2.rename(columns=abbrs_to_names2, index=abbrs_to_names2)

# Save as latex:
to_latex_with_note(
 df2, 'table_2.tex',
 caption="Statistical Test Comparisons for Model Predictions", 
 label='table:model_t_test',
 legend=legend2)
