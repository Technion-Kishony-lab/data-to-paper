
# IMPORT
import pandas as pd
from typing import Any, Dict, Optional, Tuple
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
    'Statistic': ('Chi-Square Statistic', None),
    'p-value': (None, 'Probability of observing a value as extreme as or more extreme than the observed value under the null hypothesis'),
    'DoF': ('Degrees of Freedom', 'Number of independent pieces of information that go into the calculation of a statistic'),
}

# TABLE 1:
df1 = pd.read_pickle('table_1.pkl')

# FORMAT VALUES
df1['p-value'] = df1['p-value'].apply(format_p_value)

# RENAME ROWS AND COLUMNS
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df1, k)}
abbrs_to_names, names_to_definitions = split_mapping(mapping)
df1 = df1.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(
 df1, 'table_1.tex',
 caption="Chi-square test of party-wise retweet interaction.", 
 label='table:party_wise_interaction',
 note=None,
 legend=names_to_definitions)

# TABLE 2:
df2 = pd.read_pickle('table_2.pkl')

# FORMAT VALUES
df2['p-value'] = df2['p-value'].apply(format_p_value)

# RENAME ROWS AND COLUMNS
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df2, k)} 
abbrs_to_names, names_to_definitions = split_mapping(mapping)
df2 = df2.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as Latex:
to_latex_with_note(
 df2, 'table_2.tex',
 caption="Chi-square test of state-wise retweet interaction.", 
 label='table:state_wise_interaction',
 note=None,
 legend=names_to_definitions)
