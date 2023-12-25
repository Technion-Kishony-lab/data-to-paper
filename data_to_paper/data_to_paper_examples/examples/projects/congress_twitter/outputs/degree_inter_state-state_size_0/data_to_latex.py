
# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
 'StateSize':('Representatives Volume','Number of representatives in each state'),
 'InDegree':('In-Degree','Number of incoming interactions'),
 'OutDegree':('Out-Degree','Number of outgoing interactions'),
 'Party_D_str[T.True]':('Democrat Member','Boolean, whether member is from Democrat party'),
 'Party_R_str[T.True]':('Republican Member','Boolean, whether member is from Republican party'),
 'Chamber_House_str[T.True]':('House Member','Boolean, whether member belongs to the House'),
 'Chamber_Senate_str[T.True]':('Senate Member','Boolean, whether member belongs to the Senate')
}

# TABLE 0:
df0 = pd.read_pickle('table_0.pkl')

# RENAME ROWS AND COLUMNS
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df0, k)} 
abbrs_to_names, legend = split_mapping(mapping)
df0 = df0.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(
    df0, 'table_0.tex',
    caption="Descriptive statistics of the data (mean and stddev for continuous variables, freq for categorical)", 
    label='table:descriptive_stats',
    note=None,
    legend=legend)


# TABLE 1:
df1 = pd.read_pickle('table_1.pkl')

# FORMAT VALUES
df1['p-value'] = df1['p-value'].apply(format_p_value)

# RENAME ROWS AND COLUMNS
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df1, k)} 
abbrs_to_names, legend = split_mapping(mapping)
df1 = df1.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(
 df1, 'table_1.tex',
 caption="Multiple Linear Regression: Effects of State Size, Party, and Chamber on In-Degree", 
 label='table:regression_indegree',
 note=None,
 legend=legend)


# TABLE 2:
df2 = pd.read_pickle('table_2.pkl')

# FORMAT VALUES
df2['p-value'] = df2['p-value'].apply(format_p_value)

# RENAME ROWS AND COLUMNS
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df2, k)} 
abbrs_to_names, legend = split_mapping(mapping)
df2 = df2.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(
 df2,'table_2.tex',
 caption="Multiple Linear Regression: Effects of State Size, Party, and Chamber on Out-Degree", 
 label='table:regression_outdegree',
 note=None,
 legend=legend)
