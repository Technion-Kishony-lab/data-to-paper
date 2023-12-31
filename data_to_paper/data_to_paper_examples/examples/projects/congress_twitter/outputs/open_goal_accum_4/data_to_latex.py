
# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
    'mean': ('Mean EC', 'Mean engagement count, number of Twitter interactions'),
    'std': ('Std EC', 'Standard deviation of engagement count'),
    'coef': ('Coef.', 'Coefficient from ANOVA'),
    'pvalue': (None, 'P-value'),
    'CI_lower': ('Lower 95% CI', 'Lower limit of the 95% confidence interval'),
    'CI_upper': ('Upper 95% CI', 'Upper limit of the 95% confidence interval'),
    'D': ('Democrat', None),
    'R': ('Republican', None),
    'I': ('Independent', None),
}

# TABLE 1:
df1 = pd.read_pickle('table_1.pkl')

# FORMAT VALUES
df1['mean'] = df1['mean'].apply(lambda x: round(x, 2))
df1['std'] = df1['std'].apply(lambda x: round(x, 2))

# RENAME ROWS AND COLUMNS
mapping1 = {k: v for k, v in shared_mapping.items() if is_str_in_df(df1, k)} 

abbrs_to_names1, legend1 = split_mapping(mapping1)
df1 = df1.rename(columns=abbrs_to_names1, index=abbrs_to_names1)

# Save as latex:
to_latex_with_note(
    df1, 'table_1.tex',
    caption="Mean and standard deviation of Twitter interactions of Congress members by Party and Chamber", 
    label='table:table_1',
    legend=legend1)

# TABLE 2:
df2 = pd.read_pickle('table_2.pkl')

# FORMAT VALUES 
df2['coef'] = df2['coef'].apply(lambda x: round(x, 3))
df2['pvalue'] = df2['pvalue'].apply(format_p_value)

# RENAME ROWS AND COLUMNS
mapping2 = {k: v for k, v in shared_mapping.items() if is_str_in_df(df2, k)}
mapping2.update({
    'Intercept': ('Intercept', 'ANOVA model intercept'),
    'C(Party)[T.I]': ('I Party', 'Independents compared with Democrats (reference group)'),
    'C(Party)[T.R]': ('R Party', 'Republicans compared with Democrats (reference group)'),
    'C(Chamber)[T.Senate]': ('Senate', 'Senate compared to House (reference group)'),
    'StateRepresentation': ('State Rep.', 'Number of Representatives from the state')
})

abbrs_to_names2, legend2 = split_mapping(mapping2)
df2 = df2.rename(columns=abbrs_to_names2, index=abbrs_to_names2)

# Save as latex:
to_latex_with_note(
    df2, 'table_2.tex',
    caption="ANOVA results for the effect of state representation size on Twitter interactions, controlling for party and chamber", 
    label='table:table_2',
    legend=legend2)
