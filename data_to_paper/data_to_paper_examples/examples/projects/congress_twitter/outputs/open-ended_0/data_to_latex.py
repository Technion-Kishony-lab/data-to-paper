
# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef
from typing import Dict, Tuple, Any, Optional

# PREPARATION FOR ALL TABLES
mapping: AbbrToNameDef = {
    'Chi-Squared Statistic': ('Chi-Squared Statistic', None),
    'p-value': ('p-value', 'A measure of statistical significance indicating the strength of the evidence against the null hypothesis'),
}

# TABLE 1
# Load table
df1 = pd.read_pickle('table_1.pkl')

# Apply value formatting
df1['p-value'] = df1['p-value'].apply(format_p_value)

# Apply renaming
mapping_table1 = {k: v for k, v in mapping.items() if is_str_in_df(df1, k)} 
abbrs_to_names, legend = split_mapping(mapping_table1)
df1 = df1.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex
to_latex_with_note(
 df1, 'table_1.tex',
 caption="Results of Chi-Square Independence Test for Represented State and Twitter Interactions", 
 label='table:chi_squared_test_state_interactions',
 note=None,
 legend=legend
)

# TABLE 2
# Load table
df2 = pd.read_pickle('table_2.pkl')

# Apply value formatting
df2['p-value'] = df2['p-value'].apply(format_p_value)

# Apply renaming
mapping_table2 = {k: v for k, v in mapping.items() if is_str_in_df(df2, k)}
abbrs_to_names, legend = split_mapping(mapping_table2)

df2 = df2.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex
to_latex_with_note(
 df2, 'table_2.tex',
 caption="Results of Chi-Square Independence Test for Chamber and Twitter Interactions", 
 label='table:chi_squared_test_chamber_interactions',
 note=None,
 legend=legend
)
