
# IMPORT
import pandas as pd
from typing import Dict, Any, Tuple, Optional
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
    'Party_R[T.True]': ('Republican Party', 'Membership in Republican Party, 1: Yes, 0: No'),
    'Chamber_Senate[T.True]': ('Senate', 'Membership in Senate, 1: Yes, 0: No'),
    'state_rep_count': ('State Rep. Count', 'Number of Representatives from the Same State'),
}

# TABLE 1:
df1 = pd.read_pickle('table_1.pkl')

# RENAME ROWS AND COLUMNS
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df1, k)} 
mapping |= {
    'Intercept': ('Intercept', None),
    'Beta': ('Beta', 'Regression Coefficient')
}

abb_to_names, legend = split_mapping(mapping)
df1 = df1.rename(columns=abb_to_names, index=abb_to_names)

# FORMAT P-VALUES
df1['p-value'] = df1['p-value'].apply(format_p_value)

# Save as a LaTeX table:
to_latex_with_note(
    df1, 'table_1.tex',
    caption="Regression results for variables predicting incoming interactions", 
    label='table:incoming_interactions',
    note=None,
    legend=legend)

# TABLE 2:
df2 = pd.read_pickle('table_2.pkl')

# RENAME ROWS AND COLUMNS
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df2, k)}
mapping |= {
    'Intercept': ('Intercept', None),
    'Beta': ('Beta', 'Regression Coefficient'),
}

abb_to_names, legend = split_mapping(mapping)
df2 = df2.rename(columns=abb_to_names, index=abb_to_names)

# FORMAT P-VALUES
df2['p-value'] = df2['p-value'].apply(format_p_value)

# Save as Latex:
to_latex_with_note(
    df2, 'table_2.tex',
    caption="Regression results for variables predicting outgoing interactions", 
    label='table:outgoing_interactions',
    note=None,
    legend=legend)
