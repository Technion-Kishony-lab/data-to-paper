
# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
# Define a mapping for labels that are common to all tables
shared_mapping: AbbrToNameDef = {
    'dead': ('Survival', '0: Censoring, 1: Event'),
    'sex': ('Sex', '1: Male, 2: Female'),
    'agegp': ('AgeGrp', 'Ordinal value corresponding to age group range'),
}

# TABLE 0:
df0 = pd.read_pickle('table_0.pkl')

# RENAME ROWS AND COLUMNS
mapping0 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df0, k)) 
mapping0 |= {
    'mean': ('Avg', 'Average value of Age Group'),
    'std': ('StdDv', 'Standard Deviation of the group'),
}
abbrs_to_names0, legend0 = split_mapping(mapping0)
df0 = df0.rename(columns=abbrs_to_names0, index=abbrs_to_names0)

# SAVE AS LATEX:
to_latex_with_note(
    df0, 'table_0.tex',
    caption="Descriptive statistics of age group and sex stratified by survival", 
    label='table:descriptive_statistics',
    note="Values represent mean age group value and standard deviation.",
    legend=legend0)

# TABLE 1:
df1 = pd.read_pickle('table_1.pkl')

# RENAME ROWS AND COLUMNS 
mapping1 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df1, k)) 
mapping1 |= {
    'kps': ('Krnfsky', '1: >=90, 0: <=90'),
    'stagedxn': ('Stage', '1: I-II, 3: III-IV'),
    'Intercept': ('Itcpt', 'Logistic regression model intercept'),
    'Coefficients': ('B', 'Beta Coefficients'),
    'p-value': ('P-val', 'p-value calculated from the model'),
    'Odds Ratio': ('OR', 'Odds Ratio'),  
    'Odds Ratio 2.5%': ('OR 2.5%', 'Odds Ratio 2.5% Confidence Limit'),
    'Odds Ratio 97.5%': ('OR 97.5%', 'Odds Ratio 97.5% Confidence Limit'),
    'p-value summary': ('P-val Sum', 'Summary of p-value significance'),
}
abbrs_to_names1, legend1 = split_mapping(mapping1)
df1 = df1.rename(columns=abbrs_to_names1, index=abbrs_to_names1)

# SAVE AS LATEX:
to_latex_with_note(
    df1, "table_1.tex",
    caption="Impact of age and sex on overall survival, factoring in karnofsky score and stage of organ involvement", 
    label="table:logistic_regression",
    note="Odds ratios are computed from logistic regression coefficients. P-values are given in parentheses.",
    legend=legend1)

# TABLE 2:
df2 = pd.read_pickle('table_2.pkl')

# RENAME ROWS AND COLUMNS
mapping2 = {
    'Chi-Square Test Statistic': ('ChiSquare', 'Chi-Square Test Statistic'),
    'Year of Transplant': ('Year',  '0: 2000-2004, 1: 2004-2009, 2: 2010-2014, 3: 2015-2018'),
}

abbrs_to_names2, legend2 = split_mapping(mapping2)
df2 = df2.rename(columns=abbrs_to_names2, index=abbrs_to_names2)

# SAVE AS LATEX:
to_latex_with_note(
    df2, 'table_2.tex',
    caption='Association between year of transplant and overall survival, factoring in age and gender', 
    label='table:chi_squared',
    note='Test statistic and p-value from Chi-Squared test of independence.',
    legend=legend2)
