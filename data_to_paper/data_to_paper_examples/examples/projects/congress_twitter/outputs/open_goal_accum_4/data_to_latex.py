
# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
    'Interactions': ('Int', 'Number of Twitter interactions by a member of Congress'),
    'C(Party)[T.I]': ('Independent', 'Congress Member with party affiliation as Independent (I)'),
    'C(Party)[T.R]': ('Republican', 'Congress Member with party affiliation as Republican (R)'),
    'C(Chamber)[T.Senate]': ('Senate', 'Member of Senate Chamber')
}

# TABLE 1:
df1 = pd.read_pickle('table_1.pkl')

# RENAME ROWS AND COLUMNS
mapping1 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df1, k)) 
mapping1 |= {
    'F-statistic': ('Fstat', 'F-statistic for the effect of group variance in one-way ANOVA'),
    'p-value': ('Pval', 'Probability value for F-statistic'),
}
abbrs_to_names1, legend1 = split_mapping(mapping1)
df1 = df1.rename(index=abbrs_to_names1, columns=abbrs_to_names1)

# SAVE AS LATEX:
to_latex_with_note(
    df1, 'table_1.tex',
    caption="Analysis of variance for number of interactions grouped by States", 
    label='table:anova_interactions',
    legend=legend1)

# TABLE 2:
df2 = pd.read_pickle('table_2.pkl')

# RENAME ROWS AND COLUMNS
mapping2 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df2, k)) 
mapping2 |= {
    'State_Representatives': ('RepsPerState', 'Number of representatives per state'),
    'coefficient': ('Coeff', 'Coefficient of regression analysis'),
    'p-value': ('Pval', 'Probability value for the coefficient'),
    '5% confidence interval': ('5pCentCI', 'Lower limit of confidence interval for the coefficient'),
    '95% confidence interval': ('95pCentCI', 'Upper limit of confidence interval for the coefficient'),
    'Intercept': ('Intcpt', 'Regression intercept'),
}
abbrs_to_names2, legend2 = split_mapping(mapping2)
df2 = df2.rename(index=abbrs_to_names2, columns=abbrs_to_names2)

# SAVE AS LATEX:
to_latex_with_note(
    df2, 'table_2.tex',
    caption="Regression analysis of interactions count by Party, Chamber, and the number of representatives per State", 
    label='table:regress_interactions',
    legend=legend2)
