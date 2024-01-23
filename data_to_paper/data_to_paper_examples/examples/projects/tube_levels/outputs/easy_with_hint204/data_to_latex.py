
# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES

# Common dictionary for column (row) labels that are common across the tables
shared_mapping: AbbrToNameDef = {
    'sex': ('Gender', '0: Female, 1: Male'),
    'age_c': ('Age', 'Patient age in years'),
    'ht': ('Height', 'Patient height in cm'),
    'wt': ('Weight', 'Patient weight in kg'),
    'tube_depth_G': ('OTTD', 'Optimal tracheal tube depth in cm'),
}

# TABLE 0:
df0 = pd.read_pickle('table_0.pkl')

# FORMAT VALUES 
# Not applicable in this case

# RENAME ROWS AND COLUMNS 
mapping0 = {k: v for k, v in shared_mapping.items() if is_str_in_df(df0, k)} 
mapping0 |= {
    'age_c_mean': ('Age Mean', 'Mean age in years'),
    'age_c_std': ('Age Std Dev', 'Standard deviation of age'),
    'ht_mean': ('Height Mean', 'Mean height in cm'),
    'ht_std': ('Height Std Dev', 'Standard deviation of height'),
    'tube_depth_G_mean': ('OTTD Mean', 'Mean OTTD in cm'),
    'tube_depth_G_std': ('OTTD Std Dev', 'Standard deviation of OTTD'),
    'wt_mean': ('Weight Mean', 'Mean weight in kg'),
    'wt_std': ('Weight Std Dev', 'Standard deviation of weight')
}
abbrs_to_names0, legend0 = split_mapping(mapping0)
df0 = df0.rename(index=abbrs_to_names0, columns=abbrs_to_names0)

# Transpose the DataFrame to make the table narrow
df0 = df0.T

# Convert DataFrame to LaTeX and save it in a .tex file
to_latex_with_note(
    df0, 'table_0.tex',
    caption="Descriptive statistics of age, height, weight, and OTTD, stratified by sex", 
    label='table:table_0',
    note=None,
    legend=legend0)

# TABLE 1:
df1 = pd.read_pickle('table_1.pkl')

# FORMAT VALUES 
df1['P-value'] = df1['P-value'].apply(format_p_value)

# RENAME ROWS AND COLUMNS 
mapping1 = {'P-value': ('P-value', 'Derived from t-test comparing the mean squared residuals of both models')}
abbrs_to_names1, legend1 = split_mapping(mapping1)
df1 = df1.rename(index=abbrs_to_names1, columns=abbrs_to_names1)

# Convert DataFrame to LaTeX and save it in a .tex file
to_latex_with_note(
    df1, 'table_1.tex',
    caption="Comparison of predictive power between Random Forest and Elastic Net models", 
    label='table:table_1',
    note=None,
    legend=legend1)

# TABLE 2:
df2 = pd.read_pickle('table_2.pkl')

# FORMAT VALUES
df2['P-value'] = df2['P-value'].apply(format_p_value)

# RENAME ROWS AND COLUMNS 
mapping2 = {k: v for k, v in shared_mapping.items() if is_str_in_df(df2, k)}
mapping2 |= { 'Intercept': ('Intercept', None) }
abbrs_to_names2, legend2 = split_mapping(mapping2)
df2 = df2.rename(index=abbrs_to_names2, columns=abbrs_to_names2)

# Convert DataFrame to LaTeX and save it in a .tex file
to_latex_with_note(
    df2, 'table_2.tex',
    caption="Association of age, sex, height, and weight with OTTD", 
    label='table:table_2',
    note=None,
    legend=legend2)
