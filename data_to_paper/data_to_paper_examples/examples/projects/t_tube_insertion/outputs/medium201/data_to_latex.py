
# IMPORT
import pandas as pd
from typing import Dict, Any, Tuple, Optional
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES

# Define a dictionary for the shared mapping
shared_mapping: AbbrToNameDef = {
    'age_c': ('Age', 'Patient\'s age, in years'),
    'wt': ('Weight', 'Patient\'s weight, in kg'),
    'sex': ('Sex', 'Patient\'s sex, 0: Female, 1: Male'),
    'ht': ('Height', 'Patient\'s height, in cm'),
    'tube_depth_G': ('OTTD', 'Optimal Tracheal Tube Depth, determined by chest X-ray, in cm')
}

# TABLE 0:
df = pd.read_pickle('table_0.pkl')

# RENAME ROWS AND COLUMNS
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)}
abbrs_to_names, legend = split_mapping(mapping)
df.rename(columns=abbrs_to_names, inplace=True)
df.rename(index=abbrs_to_names, inplace=True)

# Save Table 0 as latex
to_latex_with_note(df, 'table_0.tex', 
                   caption='Descriptive statistics of age and weight, stratified by sex', 
                   label='table:table_0',
                   legend=legend)

# TABLE 1:
df = pd.read_pickle('table_1.pkl')

# FORMAT VALUES
df['p-value'] = df['p-value'].apply(format_p_value)

# RENAME ROWS AND COLUMNS
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)} 
mapping['t-statistic'] = ('t-statistic', None)
mapping['p-value'] = ('p-value', 'p-value for the t-test of the difference between residuals of the two models')
abbrs_to_names, legend = split_mapping(mapping)
df.rename(columns=abbrs_to_names, inplace=True)

# Save as latex
to_latex_with_note(df, 'table_1.tex', 
                   caption='Comparison of the performance of the machine learning model and the formula-based model for predicting OTTD', 
                   label='table:table_1',
                   note='', 
                   legend=legend)
