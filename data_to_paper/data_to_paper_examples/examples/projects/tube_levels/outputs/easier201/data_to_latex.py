

# IMPORT
import pandas as pd
from typing import Dict, Any, Tuple, Optional
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
 'residual_height_model': ('Residuals for Height Model', 'Square residuals for the Height Model, cm²'),
 'residual_age_model': ('Residuals for Age Model', 'Square residuals for the Age Model, cm²'),
}

# TABLE 1:
df = pd.read_pickle('table_1.pkl')

# RENAME ROWS AND COLUMNS
mapping: AbbrToNameDef = {
key: val for key, val in shared_mapping.items() if is_str_in_df(df, key)
}
mapping |= {
 'mean': ('Mean', 'Average of the square residuals'),
 'std': ('Std. deviation', 'Standard deviation of the square residuals'),
}

abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(
 df, 'table_1.tex',
 caption="Square residuals for the Height Model and the Age Model",
 label='table:residuals',
 note="Table values are in cm²",
 legend=legend)

# TABLE 2:
df = pd.read_pickle('table_2.pkl')

# FORMAT VALUES
df['p-value'] = df['p-value'].apply(format_p_value)

# RENAME ROWS AND COLUMNS 
mapping: AbbrToNameDef = {
 'T-Statistic': ('T-Statistic', 'Test statistic from the paired t-test'),
 'p-value': ('P-value', 'P-value from the paired t-test'),
 'Paired T-Test': ('Test', None),
}
abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(
 df, 'table_2.tex',
 caption="Paired t-test results for residuals of the Height and Age Models", 
 label='table:t_test',
 note=None,
 legend=legend)
