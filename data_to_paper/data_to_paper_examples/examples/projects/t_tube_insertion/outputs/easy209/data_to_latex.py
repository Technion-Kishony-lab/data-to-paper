
# IMPORT
import pandas as pd
from typing import Dict, Any, Tuple, Optional
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES

shared_mapping: AbbrToNameDef = {
 'sex': ('Sex', '0: Female, 1: Male'),
 'mean': ('Mean OTTD', 'Average optimal tracheal tube depth, cm'),
 'std': ('Std OTTD', 'Standard deviation of optimal tracheal tube depth, cm'),
 'Model': (None, 'ML Model: Random Forest or Elastic Net'),
 'Mean Squared Error': ('MSE', 'Mean Squared Error of ML Model prediction'),
 'Paired t-test': (None, 'Paired t-test statistic or p-value'),
 'Values': (None, 'Values of Paired t-test statistic or p-value')
}

# TABLE 0:
df = pd.read_pickle('table_0.pkl')

# RENAME ROWS AND COLUMNS 
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)} 
abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(
 df, 'table_0.tex',
 caption="Descriptive statistics of optimal tracheal tube depth stratified by sex.", 
 label='table:stat_gender',
 legend=legend)

# TABLE 1:
df = pd.read_pickle('table_1.pkl')

# RENAME ROWS AND COLUMNS 
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)} 
abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(
 df, 'table_1.tex',
 caption="Performance metrics of the Random Forest and Elastic Net models", 
 label='table:model_performance',
 legend=legend)


# TABLE 2
df = pd.read_pickle('table_2.pkl')

# FORMAT P-VALUE
# Apply format_p_value only to the p-value row 
df.loc[df.index == 'p-value', 'Values'] = df.loc[df.index == 'p-value', 'Values'].apply(format_p_value)

# RENAME ROWS AND COLUMNS 
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)} 
abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(
 df, 'table_2.tex',
 caption="Paired t-test comparing the performance of the Random Forest and Elastic Net models.", 
 label='table:model_comparison',
 legend=legend)


