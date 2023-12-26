

# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES

# Shared mapping
shared_mapping: AbbrToNameDef = {
    'F Stat': ('F statistic', None),
    'p-value': ('p-value', 'value of the statistical significance test'),
    'Party': ('Political Party', 'D: Democrat, R: Republican, I: Independent'),
    'Average Degree Centrality': ('Average Degree Centrality', 'Average centrality measure indicating the proportion of out-degree interaction within the Twitter network'),
    'D': ('Democrat', None),
    'I': ('Independent', None),
    'R': ('Republican', None)
}

# TABLE 1
df1 = pd.read_pickle('table_1.pkl')

# Format statistical significance values
df1['p-value'] = df1['p-value'].apply(format_p_value)

# Rename rows and columns
mapping1 = {k: v for k, v in shared_mapping.items() if is_str_in_df(df1, k)}
abbrs_to_names1, legend1 = split_mapping(mapping1)
df1 = df1.rename(columns=abbrs_to_names1, index=abbrs_to_names1)

# Save as latex
to_latex_with_note(
 df1, 
 'table_1.tex',
 caption="ANOVA test of association between chamber affiliation and out-degree centrality", 
 label='table:anova_1',
 note="Out-degree centrality is a measure of the proportion of all other congress members a given member interacts with on Twitter.",
 legend=legend1
)

# TABLE 2
df2 = pd.read_pickle('table_2.pkl')

# Rename rows and columns
mapping2 = {k: v for k, v in shared_mapping.items() if is_str_in_df(df2, k)}
abbrs_to_names2, legend2 = split_mapping(mapping2)
df2 = df2.rename(index=abbrs_to_names2)

# Save as latex
to_latex_with_note(
 df2, 
 'table_2.tex',
 caption="Degree centrality by political party", 
 label='table:degree_centrality_party',
 note=None,
 legend=legend2
)
