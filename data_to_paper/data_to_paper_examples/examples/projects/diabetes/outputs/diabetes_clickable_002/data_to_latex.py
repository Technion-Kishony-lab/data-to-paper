

# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
    'Diabetes_binary': ('Diabetes', 'Diabetes occurrence. 1 if yes, 0 otherwise'),
    'BMI': ('BMI', None),
    'Age': ('Age', '13-level age category in intervals of 5 years (e.g., 1 = 18-24, 2 = 25-29)'),
    'Sex': ('Gender', '1 if male, 0 if female'),
    'Education': ('Education', 'Education Level. 1-6 with 1 being "Never attended school" and 6 being "College Graduate"'),
    'Income': ('Income', 'Income Scale. 1-8 with 1 being "<=$10K" and 8 being ">$75K"'),
    't': ('t-val', 't-statistic of the regression estimate'),
    'P>|t|': ('p-val', 'Probability that the null hypothesis (of no relationship) produces results as extreme as the estimate')
}

# TABLE 0:
df0 = pd.read_pickle('table_0.pkl')

# DEDUPLICATE INFORMATION 
count_unique = df0["count"].unique()
assert len(count_unique) == 1
df0 = df0.drop(columns=["count"])

# RENAME ROWS AND COLUMNS 
mapping0 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df0, k)) 
mapping0['PhysActivity'] = ('Physical Activity', 'Phys. Activity in past 30 days, 1: Yes, 0: No')

abbrs_to_names0, legend0 = split_mapping(mapping0)
df0 = df0.rename(columns=abbrs_to_names0, index=abbrs_to_names0)

# SAVE AS LATEX
to_latex_with_note(
    df0, 'table_0.tex',
    caption="Descriptive statistics of key variables", 
    label='table:desc_stats',
    note=f"NOTE: The number of observations in all variables is {count_unique[0]}",
    legend=legend0)

# TABLE 1:
df1 = pd.read_pickle('table_1.pkl')

# RENAME ROWS AND COLUMNS
mapping1 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df1, k))
mapping1['BMI:PhysActivity'] = ('BMI * Phys. Act.', 'Interaction between BMI and Physical Activity')
mapping1['PhysActivity'] = ('Physical Activity', 'Phys. Activity in past 30 days, 1: Yes, 0: No')

abbrs_to_names1, legend1 = split_mapping(mapping1)
df1 = df1.rename(columns=abbrs_to_names1, index=abbrs_to_names1)

# SAVE AS LATEX:
to_latex_with_note(
    df1, 'table_1.tex',
    caption="Analysis of relationship between BMI and Diabetes moderated by Physical Activity", 
    label='table:bmi_physactivity',
    legend=legend1)

# TABLE 2:
df2 = pd.read_pickle('table_2.pkl')

# RENAME ROWS AND COLUMNS
mapping2 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df2, k))
mapping2['Smoker'] = ('Smoker', '1 if smoker, 0 otherwise')
mapping2['BMI:Smoker'] = ('BMI * Smoker', 'Interaction between BMI and Smoking')

abbrs_to_names2, legend2 = split_mapping(mapping2)
df2 = df2.rename(columns=abbrs_to_names2, index=abbrs_to_names2)

# SAVE AS LATEX:
to_latex_with_note(
    df2, 'table_2.tex',
    caption="Analysis of relationship between BMI and Diabetes moderated by Smoking Status", 
    label='table:bmi_smoking',
    legend=legend2)


# TABLE 3:
df3 = pd.read_pickle('table_3.pkl')

# RENAME ROWS AND COLUMNS
mapping3 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df3, k))
mapping3['Fruits'] = ('Fruits', 'One fruit/day, 1: Yes, 0: No')
mapping3['Veggies'] = ('Veggies', 'One veggie/day, 1: Yes, 0: No')
mapping3['BMI:Fruits'] = ('BMI * Fruits', 'Interaction between BMI and Fruit consumption')
mapping3['BMI:Veggies'] = ('BMI * Veggies', 'Interaction between BMI and Vegetable consumption')

abbrs_to_names3, legend3 = split_mapping(mapping3)
df3 = df3.rename(columns=abbrs_to_names3, index=abbrs_to_names3)

# SAVE AS LATEX:
to_latex_with_note(
    df3, 'table_3.tex',
    caption="Analysis of relationship between BMI and Diabetes moderated by Consumption of Fruits and Vegetables", 
    label='table:bmi_fruits_veggies',
    legend=legend3)
    
