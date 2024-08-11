
# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
shared_mapping : AbbrToNameDef = {
   'age': ('Age', 'Age, years'),
   'BMI_numeric': ('BMI', 'Body Mass Index, 0: Under 30, 1: Over 30'),
}

# TABLE 0:
df0 = pd.read_pickle('table_0.pkl')

# RENAME ROWS AND COLUMNS
mapping0: AbbrToNameDef = {
    'coef': ('Coefficient', None),
    'std_err': ('Standard Error', None),
    'p_value': ('P-value', None),
}
mapping0 = {**mapping0, **shared_mapping}
abbrs_to_names0, legend0 = split_mapping(mapping0)
df0 = df0.rename(columns=abbrs_to_names0, index=abbrs_to_names0)

# SAVE AS LATEX
to_latex_with_note(
   df0, 'table_0.tex',
   caption="Descriptive statistics of age and body mass index stratified by sex", 
   label='table:descriptive_statistics',
   legend=legend0)


# TABLE 1:
df1 = pd.read_pickle('table_1.pkl')

# RENAME ROWS AND COLUMNS
mapping1: AbbrToNameDef = {
   'coef': ('Coefficient', None),
   'std_err': ('Standard Error', None),
   'p_value': ('P-value', None),
   'group_factorized': ('Group', 'Vaccination Status - 0: None, 1: Vaccinated, 2: Infected, 3: Hybrid immunity'),
   'sex_factorized': ('Sex', '0: Female, 1: Male')
}
mapping1 = {**mapping1, **shared_mapping}
abbrs_to_names1, legend1 = split_mapping(mapping1)
df1 = df1.rename(columns=abbrs_to_names1, index=abbrs_to_names1)

# SAVE AS LATEX
to_latex_with_note(
   df1, 'table_1.tex',
   caption="Multiple regression analysis with the symptom number as the dependent variable", 
   label='table:multiple_regression',
   legend=legend1)

# TABLE 2:
df2 = pd.read_pickle('table_2.pkl')

# RENAME ROWS AND COLUMNS
mapping2: AbbrToNameDef = {
   'mean': ('Mean', None),
   'std': ('Standard Deviation', None)
}
abbrs_to_names2, legend2 = split_mapping(mapping2)
df2 = df2.rename(columns=abbrs_to_names2, index=abbrs_to_names2)

# SAVE AS LATEX
to_latex_with_note(
   df2, 'table_2.tex',
   caption="Descriptive statistics of symptom number grouped by group and body mass index", 
   label='table:grouped_statistics')
