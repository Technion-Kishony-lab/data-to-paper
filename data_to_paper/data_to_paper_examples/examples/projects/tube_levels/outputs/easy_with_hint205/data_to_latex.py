
# IMPORT
import pandas as pd
from typing import Any, Dict, Optional, Tuple
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
    'Mean Squared Residuals': ('Avg. Sq. Residuals', 'Average of the squared residuals'),
    'Std. Dev. Squared Residuals': ('Std. Sq. Residuals', 'Standard deviation of the squared residuals'),
    'Random Forest': ('RF', 'Random Forest Machine Learning Model'),
    'Elastic Net': ('EN', 'Elastic Net Machine Learning Model'),
    'Hyperparameters': ('Parameters', 'Optimal model parameters found via grid search'),
}

# TABLE 1:
df1 = pd.read_pickle('table_1.pkl')

# RENAME ROWS AND COLUMNS 
mapping_table_1 = {k: v for k, v in shared_mapping.items() if is_str_in_df(df1, k)} 
abbrs_to_names, legend = split_mapping(mapping_table_1)
df1 = df1.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(
 df1, 
 'table_1.tex',
 caption="Summary statistics of the squared residuals for test datasets using the RF and EN models.", 
 label='table:summary_statistics',
 legend=legend)

# TABLE 2:
df2 = pd.read_pickle('table_2.pkl')

# Transpose df2 to make it narrower
df2 = df2.T

# RENAME ROWS AND COLUMNS 
mapping_table_2 = {k: v for k, v in shared_mapping.items() if is_str_in_df(df2, k)}
abbrs_to_names, legend = split_mapping(mapping_table_2)
df2 = df2.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(
 df2, 
 'table_2.tex',
 caption="Optimal hyperparameters for the RF and EN models.", 
 label='table:hyperparameters',
 legend=legend)
