
# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
    'wt': ('Weight', 'Weight of patient in kilograms'),
    'tube_depth_G': ('OTTD', 'Optimal tracheal tube depth as determined by chest X-ray (in cm)'),
    'sex': ('Sex', 'Patient sex (0=Female, 1=Male)'),
    'tube': ('Tube ID', 'Internal diameter of the tube in milimeters'),
    'age_c': ('Age', 'Patient age (in years, rounded to half years)'),
    'ht': ('Height','Patient height in centimeters'),
}

# TABLE 0
df0 = pd.read_pickle('table_0.pkl')

# RENAME ROWS AND COLUMNS
mapping0 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df0, k))
abbrs_to_names0, legend0 = split_mapping(mapping0)
df0 = df0.rename(columns=abbrs_to_names0, index=abbrs_to_names0)

# SAVE AS LATEX
to_latex_with_note(
    df0, 'table_0.tex',
    caption='Descriptive statistics of weight stratified by sex.', 
    label='table:descriptive_sex_weight',
    note=None,
    legend=legend0)


# TABLE 1
df1 = pd.read_pickle('table_1.pkl')

# RENAME ROWS AND COLUMNS
mapping1 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df1, k)) 
mapping1 |= {
    'coef': ('Coefficient', None),
    'ci_low': ('CI Lower','95% Confidence interval lower limit'),
    'ci_high': ('CI Upper','95% Confidence interval upper limit'),
    'pval': ('P-value', 'Statistical significance level'),
    'std err': ('Std Error', 'Standard Error'),
    'Weight:Sex': ('Weight:Sex', 'Interaction term between Weight and Sex'),
}
abbrs_to_names1, legend1 = split_mapping(mapping1)
df1 = df1.rename(columns=abbrs_to_names1, index=abbrs_to_names1)

# SAVE AS LATEX
to_latex_with_note(
    df1, 'table_1.tex',
    caption="Linear regression model with interaction between weight and sex predicting OTTD.",
    label='table:linear_regression_model',
    note=None,
    legend=legend1)


# TABLE 2
df2 = pd.read_pickle('table_2.pkl')

# RENAME ROWS AND COLUMNS
mapping2 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df2, k)) 
mapping2 |= {
    'coef': ('Coefficient', None),
    'ci_low': ('CI Lower','95% Confidence interval lower limit'),
    'ci_high': ('CI Upper','95% Confidence interval upper limit'),
    'pval': ('P-value', 'Statistical significance level'),
    'std err': ('Std Error', 'Standard Error'),
}
abbrs_to_names2, legend2 = split_mapping(mapping2)
df2 = df2.rename(columns=abbrs_to_names2, index=abbrs_to_names2)

# SAVE AS LATEX
to_latex_with_note(
    df2, 'table_2.tex',
    caption="Polynomial regression model with weight predicting OTTD.",
    label='table:poly_regression_model',
    note=None,
    legend=legend2)
