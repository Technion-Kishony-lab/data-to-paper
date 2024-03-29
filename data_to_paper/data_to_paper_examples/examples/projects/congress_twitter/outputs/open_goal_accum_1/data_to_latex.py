

# IMPORT:
import pandas as pd
from typing import Dict, Optional, Tuple
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES:
shared_mapping: AbbrToNameDef = {
    'Party': ('Party Affiliation', 'Political party, D=Democrat, R=Republican, I=Independent'),
    'Observed': ('Observed Frequency', 'Number of observed twitter interactions'),
    'Expected': ('Expected Frequency', 'Number of expected twitter interactions'),
    'Chi-Sq statistic': ('Chi-Sq Statistic', 'Chi-Square statistic for the distribution of the data'),
    'P-value': ('P-value', 'The probability of obtaining observed data given the null hypothesis is true'),
    'D': ('Democrat', 'Member of the Democratic Party'),
    'R': ('Republican', 'Member of the Republican Party'),
    'I': ('Independent', 'Independent member'),
}

# TABLE 1:
df1 = pd.read_pickle('table_1.pkl')

df1['P-value'] = df1['P-value'].apply(format_p_value)

mapping1 = {k: v for k, v in shared_mapping.items() if is_str_in_df(df1, k)}
abbrs_to_names, legend = split_mapping(mapping1)
df1 = df1.rename(columns=abbrs_to_names, index=abbrs_to_names)

to_latex_with_note(
 df1, 'table_1.tex',
 caption="Chi-Square Test of Association Between Party Affiliation and Twitter Interactions", 
 label='table:chi_sq_party',
 note="All P-values are two-sided",
 legend=legend)

# TABLE 2:
df2 = pd.read_pickle('table_2.pkl')

shared_mapping.update({
    'sum_sq': ('Sum of Squares', 'Sum of the squares of each observation from the mean'),
    'df': ('Degree of Freedom', 'Total number of observations minus the number of independent constraints'),
    'F': ('F-Statistic', 'A statistic calculated by an ANOVA test'),
    'PR(>F)': ('P-value', 'The probability of obtaining observed data given the null hypothesis is true'),
})

mapping2 = {k: v for k, v in shared_mapping.items() if is_str_in_df(df2, k)}
abbrs_to_names, legend = split_mapping(mapping2)
df2 = df2.rename(columns=abbrs_to_names, index=abbrs_to_names)

if 'P-value' in df2.columns:
    df2['P-value'] = df2['P-value'].apply(format_p_value)

to_latex_with_note(
 df2, 'table_2.tex',
 caption="ANOVA Test of Association Between State and Twitter Interactions", 
 label='table:anova_state',
 note="All P-values are two-sided",
 legend=legend)
 
