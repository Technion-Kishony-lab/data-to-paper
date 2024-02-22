
# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, is_str_in_df, split_mapping, AbbrToNameDef
from typing import Optional, Dict, Any, Tuple

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
    'Coef.': ('Coeff.', 'Coefficient of the logistic regression model'),
    'Std.Err.': ('Std. Err.', None),
    'P>|z|': ('Pval', 'P-value'),
    '[0.025': ('CI LB', '95% Confidence Interval Lower Bound'),
    '0.975]': ('CI UB', '95% Confidence Interval Upper Bound'),
    'Age': (None, '13-level age category'),
    'BMI': (None, 'Body Mass Index'),
    'Income': (None, 'Income level, 1 to 8'),
    'Education': (None, 'Education level, 1 to 6'),
    'HighBP': (None, 'High Blood Pressure (0=no, 1=yes)'),
    'HighChol': (None, 'High Cholesterol (0=no, 1=yes)'),
    'PhysActivity': (None, 'Physical Activity in past 30 days (0=no, 1=yes)'),
    'z': ('z-stat', None),
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
    caption="Descriptive Statistics of Physical Activity Stratified by Diabetes Presence", 
    label='table:desc_stats',
    legend=legend0)


# TABLE 1:
df1 = pd.read_pickle('table_1.pkl')

# RENAME ROWS AND COLUMNS
mapping1 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df1, k)) 
abbrs_to_names1, legend1 = split_mapping(mapping1)
df1 = df1.rename(columns=abbrs_to_names1, index=abbrs_to_names1)

# SAVE AS LATEX:
to_latex_with_note(
    df1, 'table_1.tex',
    caption="Association Between Physical Activity and Diabetes Prevalence", 
    label='table:assoc_pa_diabetes',
    legend=legend1)


# TABLE 2:
df2 = pd.read_pickle('table_2.pkl')

# RENAME ROWS AND COLUMNS
mapping2 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df2, k)) 
mapping2 |= {
    'PhysActivity:BMI': ('PA * BMI', 'Interaction term, Physical Activity and BMI'),
}
abbrs_to_names2, legend2 = split_mapping(mapping2)
df2 = df2.rename(columns=abbrs_to_names2, index=abbrs_to_names2)

# SAVE AS LATEX:
to_latex_with_note(
    df2, 'table_2.tex',
    caption="Moderating Effect of BMI on the Association Between Physical Activity and Diabetes Prevalence", 
    label='table:mod_effect',
    legend=legend2)
