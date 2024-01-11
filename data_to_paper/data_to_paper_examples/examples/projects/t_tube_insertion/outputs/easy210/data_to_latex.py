
# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
 'rf_residuals_mean': ('RF Mean', 'Mean of residuals from Random Forest model'),
 'rf_residuals_std': ('RF Std.', 'Standard Deviation of residuals from Random Forest model'),
 'en_residuals_mean': ('EN Mean', 'Mean of residuals from Elastic Net model'),
 'en_residuals_std': ('EN Std.', 'Standard Deviation of residuals from Elastic Net model'),
}

# TABLE 1
df = pd.read_pickle('table_1.pkl')
df = df.T # transposing the dataframe

# RENAME ROWS AND COLUMNS
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)}
abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex
to_latex_with_note(
 df, 'table_1.tex',
 caption="Summary of residuals from the Random Forest and Elastic Net models (Transposed)", 
 label='table:summary_of_residuals',
 legend=legend
)

# TABLE 2
df = pd.read_pickle('table_2.pkl')

# FORMAT VALUES
df['p_value'] = df['p_value'].apply(format_p_value)

# RENAME ROWS AND COLUMNS
mapping = {
 't_statistic': ('T-Stat', 'The calculated T-statistic from the paired T-test'),
 'p_value': ('P-value', 'The significance of the paired T-test'),
}

abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex
to_latex_with_note(
 df, 'table_2.tex',
 caption="T-test results for Random Forest and Elastic Net models", 
 label='table:ttest',
 legend=legend
)
