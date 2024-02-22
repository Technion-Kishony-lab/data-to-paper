

# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, is_str_in_df, split_mapping, AbbrToNameDef
from typing import Dict, Any, Tuple, Optional

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
    'PhysActivity': ('Phys. Act.', '0: Inactive, 1: Active'),
    'HighBP': ('High BP', '0: No, 1: Yes'),
    'HighChol': ('High Chol.', '0: No, 1: Yes'),
    'HeartDiseaseorAttack': ('Heart Disease', '0: No, 1: Yes'),
    'No': ('No', 'Individuals without Diabetes'),
    'z': ('Z-score', 'Standard Score or Z-score is a metric that describes a values relationship to the mean of a group of values.')
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
    caption="Descriptive statistics of Physical Activity and Chronic Health Conditions stratified by Diabetes status", 
    label='table:descriptive_statistics',
    note="Values represent frequency distributions",
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
    caption="Association between physical activity and high blood pressure among diabetics", 
    label='table:association_highBP',
    note="Values represent logistic regression coefficients",
    legend=legend1)

# TABLE 2:
df2 = pd.read_pickle('table_2.pkl')

# RENAME ROWS AND COLUMNS 
mapping2 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df2, k)) 
abbrs_to_names2, legend2 = split_mapping(mapping2)
df2 = df2.rename(columns=abbrs_to_names2, index=abbrs_to_names2)

# SAVE AS LATEX:
to_latex_with_note(
    df2, 'table_2.tex',
    caption="Association between physical activity and high cholesterol among diabetics", 
    label='table:association_highChol',
    note="Values represent logistic regression coefficients",
    legend=legend2)

# TABLE 3:
df3 = pd.read_pickle('table_3.pkl')

# RENAME ROWS AND COLUMNS 
mapping3 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df3, k)) 
abbrs_to_names3, legend3 = split_mapping(mapping3)
df3 = df3.rename(columns=abbrs_to_names3, index=abbrs_to_names3)

# SAVE AS LATEX:
to_latex_with_note(
    df3, 'table_3.tex',
    caption="Association between physical activity and heart disease among diabetics", 
    label='table:association_coronary',
    note="Values represent logistic regression coefficients",
    legend=legend3)

