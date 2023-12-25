

# IMPORT
import pandas as pd
from typing import Any, Dict, Optional, Tuple
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {}

# TABLE 0:
df0 = pd.read_pickle('table_0.pkl')
mapping0 = {
    'state_size': ('State Size', 'Number of congress members from the state')
}
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df0, k)}
mapping |= mapping0
abbrs_to_names, legend = split_mapping(mapping)
df0 = df0.rename(columns=abbrs_to_names, index=abbrs_to_names)

to_latex_with_note(
 df0, 
 'table_0.tex', 
 caption="Descriptive statistics of state size.", 
 label='table:table0',
 legend=legend)


# TABLE 1:
df1 = pd.read_pickle('table_1.pkl')
df1['P-values']= df1['P-values'].apply(format_p_value)

mapping1 = {
    'P-values':('P-values', 'P-values from the logistic regression (<1e-06 if smaller)'),
    'C(source_party)[D]':('Democrat', 'Democratic party'),
    'C(source_party)[I]':('Independent', 'Independent party'),
    'C(source_party)[R]':('Republican', 'Republican party'),
    'C(source_chamber)[T.Senate]':('Senate', 'The Senate chamber'),
    'source_state_size_norm':('Normalized State Size', 'Normalized by the size of the state')
}
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df1, k)} 
mapping |= mapping1
abbrs_to_names, legend = split_mapping(mapping)
df1 = df1.rename(index=abbrs_to_names)

to_latex_with_note(
 df1, 
 'table_1.tex', 
 caption="Logistic regression results for the influence of state size, party, and chamber on interactions.", 
 label='table:table1',
 note="Coefficients are derived from logistic regression and represent the influence of each term on the likelihood of congress members' interaction.", 
 legend=legend)

