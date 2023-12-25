
# IMPORT
import pandas as pd
from typing import Optional, Dict, Tuple
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES

# TABLE 0:
df0 = pd.read_pickle('table_0.pkl')

# RENAME ROWS AND COLUMNS
mapping0: AbbrToNameDef = {
 'Size': ('Size', 'Number of Congress members from the same state'),
 'InDegree': ('In', 'Number of Twitter interactions received'),
 'OutDegree': ('Out', 'Number of Twitter interactions initiated'),
 'D': ('Democrat', None),
 'R': ('Republican', None),
 'I': ('Independent', None)
}
abbrs_to_names, legend = split_mapping(mapping0)
df0 = df0.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(
 df0, 'table_0.tex',
 caption="Descriptive stats of Size, In, and Out stratified by Party and Chamber", 
 label='table:desc_stats_party_chamber',
 note=None,
 legend=legend)

# TABLE 1:
df1 = pd.read_pickle('table_1.pkl')

# FORMAT VALUES
df1[['pvalue_in_degree', 'pvalue_out_degree']] = df1[['pvalue_in_degree', 'pvalue_out_degree']].applymap(format_p_value)

# RENAME ROWS AND COLUMNS
mapping1: AbbrToNameDef = {
 'coef_in_degree': ('In Coef', None),
 'coef_out_degree': ('Out Coef', None),
 'pvalue_in_degree': ('In P-value', None),
 'pvalue_out_degree': ('Out P-value', None),
 'Size': ('Size', 'Number of Congress members from the same state'),
 'C(Chamber)[T.Senate]': ('Sen', 'The member is part of the Senate'),
 'C(Party)[T.R]': ('GOP', 'The member is from the Republican Party'),
 'C(Party)[T.I]': ('Ind', 'The member is Independent')
}
abbrs_to_names, legend = split_mapping(mapping1)
df1 = df1.rename(index=abbrs_to_names, columns=abbrs_to_names)

# Save as latex:
to_latex_with_note(
 df1, 'table_1.tex',
 caption="Regression analysis of incoming and outgoing interactions, state size as independent variable, adjusted for Party and Chamber", 
 label='table:regression_state_size_interaction',
 note=None,
 legend=legend)
