
# IMPORT
import pandas as pd
from typing import Dict, Any, Optional, Tuple
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
    'RMSE': ('Root Mean Sq. Err.', 'Root mean square error, in cm'),
    'Best Params': (None, 'Hyperparameters that produced the smallest cross-validated RMSE')
}

# TABLE 1:
df = pd.read_pickle('table_1.pkl')

# FORMAT VALUES 
# No value formatting needed.

# RENAME ROWS AND COLUMNS
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)} 
mapping |= {
    'Random Forest': ('RF', 'Random Forest model'),
    'Elastic Net': ('EN', 'Elastic Net model')
}
abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(
 df, 'table_1.tex',
 caption="Performance summary of two Machine-Learning models", 
 label='table:performance_summary',
 note="Target variable is OTTD, optimal tracheal tube depth, in cm.",
 legend=legend)

# TABLE 2:
df = pd.read_pickle('table_2.pkl')

# FORMAT VALUES 
# 'T-statistic' row is not a p-value, hence we should only apply format_p_value to the 'p-value' row.
df.loc['p-value', 'Value'] = format_p_value(df.loc['p-value', 'Value'])

# RENAME ROWS AND COLUMNS
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)} 
mapping |= {
    'T-statistic': (None, 'Statistic from a paired t-test of the squared residuals of the RF and EN models'),
    'p-value': ('P-value', 'Two-tailed P-value from the above t-test')
}
abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(
 df, 'table_2.tex',
 caption="Paired t-test results for squared residuals of RF and EN models", 
 label='table:t_test_results',
 note="Models compared are RF and EN. The alternative hypothesis is that the mean squared residual of the RF model is different from that of the EN model.",
 legend=legend)
