
# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
    'sex': ('Sex', '0: Female, 1: Male'),
    'age_c': ('Age (Years)', None),
    'ht': ('Height (cm)', None),
    'wt': ('Weight (kg)', None),
    'depth_formula_age': ('Age-based OTTD (cm)', 'Optimal tracheal tube depth based on age'),
    'depth_formula_height': ('Height-based OTTD (cm)', 'Optimal tracheal tube depth based on height'),
    'depth_formula_tube': ('Tube-based OTTD (cm)', 'Optimal tracheal tube depth based on tube ID size'),
}

# TABLE 0:
df0 = pd.read_pickle('table_0.pkl')

# RENAME ROWS AND COLUMNS
mapping0 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df0, k)) 
abbrs_to_names0, legend0 = split_mapping(mapping0)
df0 = df0.rename(columns=abbrs_to_names0, index=abbrs_to_names0)

# SAVE AS LATEX:
to_latex_with_note(
    df0, 'table_0.tex',
    caption="Descriptive statistics of sex, age, height, and weight stratified by sex.", 
    label='table:DescriptiveStatistics',
    legend=legend0
)


# TABLE 1:
df1 = pd.read_pickle('table_1.pkl')

# RENAME ROWS AND COLUMNS
mapping1 = {
    'MSE ML Model': ('ML MSE', 'Mean Squared Error of Machine Learning Models'),
    'MSE Formula': ('F. MSE', 'Mean Squared Error of Formula-based Methods'),
    'p-value': ('p-val.', 'p-value for hypothesis testing'),
}

# Modify df1 Index
new_index = [i.replace('vs', 'Vs F').replace('_', ' ') for i in df1.index] # Shorten comparison labels and replace "_" with " "
df1.rename(index=dict(zip(df1.index, new_index)), inplace=True)
abbrs_to_names1, legend1 = split_mapping(mapping1)
df1.rename(columns=abbrs_to_names1, inplace=True)

# SAVE AS LATEX:
to_latex_with_note(
    df1, 'table_1.tex',
    caption="Comparison of Mean Squared Error (MSE) and p-value for ML models and formulas.", 
    label='table:MLEComparison',
    legend=legend1
)
