
# IMPORT
import pandas as pd
import pickle
from typing import Dict, Tuple, Any, Optional
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
# Define shared mapping
shared_mapping: AbbrToNameDef = {
 'ht': ('Height', 'Height(cm)'),
 'age_c': ('Age', 'Age(years)'),
 'sex': ('Sex', '0: Female, 1: Male'),
 'tube_depth_G': ('OTTD', 'Optimal Tracheal Tube Depth(cm)')
}

# TABLE 0
df0 = pd.read_pickle('table_0.pkl')

# Format Values
# No formatting of values in this table.

# Rename Rows and Columns
mapping0 = {k: v for k, v in shared_mapping.items() if is_str_in_df(df0, k)}
abbrs_to_names, legend = split_mapping(mapping0)
df0 = df0.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex
to_latex_with_note(df0, 'table0.tex',
  caption='Descriptive statistics of Height and Age stratified by Sex',
  label='table:descr_stats_height_age',
  legend=legend)

# TABLE 1
df1 = pd.read_pickle('table_1.pkl')

# Format Values
df1['p-value'] = df1['p-value'].apply(format_p_value)

# Rename Rows and Columns
mapping1 = {k: v for k, v in shared_mapping.items() if is_str_in_df(df1, k)}
# Add 'ML Model' to mapping1
mapping1['ML Model'] = ('ML Model', 'Machine Learning Model') 
abbrs_to_names, legend = split_mapping(mapping1)
df1 = df1.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex
to_latex_with_note(df1, 'table1.tex',
  caption='Comparison of predictive power: ML Model vs. Formula-based Model',
  label='table:compare_ML_FBM',
  legend=legend)
