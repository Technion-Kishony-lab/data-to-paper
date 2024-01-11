
# IMPORT
import pandas as pd
from typing import Dict, Any, Optional, Tuple

# import 
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
AbbrToNameDef = Dict[Any, Tuple[Optional[str], Optional[str]]]

shared_mapping: AbbrToNameDef = {
 'sex': ('Sex', 'Patient sex (0=female, 1=male)'),
 'age_c': ('Age', 'Patient age (years, rounded to half years)'),
 'ht': ('Height', 'Patient height (cm)'),
 'wt': ('Weight', 'Patient weight (kg)'),
 'tube_depth_G': ('OTTD', 'Optimal tracheal tube depth as determined by chest X-ray (in cm)'),
 'RF_MSE': ('RF MSE', 'Random Forest model - Mean Square Error'),
 'EN_MSE': ('EN MSE', 'Elastic Net model - Mean Square Error')
}

# TABLE 0:
df = pd.read_pickle('table_0.pkl')

# RENAME ROWS AND COLUMNS
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)} 
abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(
 df, 'table_0.tex',
 caption="Descriptive Statistics of Age, Sex, Height, Weight, and OTTD", 
 label='table:stat_desc_0',
 note="",
 legend=legend)

# TABLE 1:
df = pd.read_pickle('table_1.pkl')

# RENAME ROWS AND COLUMNS
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)} 
abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(
 df, 'table_1.tex',
 caption="Descriptive Statistics of Age, Sex, Height, Weight, and OTTD", 
 label='table:stat_desc_1',
 note="",
 legend=legend)

# TABLE 2:
df = pd.read_pickle('table_2.pkl')

# RENAME ROWS AND COLUMNS
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)} 
abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(
 df, 'table_2.tex',
 caption="Random Forest Model Performance: Mean Square Error", 
 label='table:rf_model_performance',
 note="",
 legend=legend)

# TABLE 3:
df = pd.read_pickle('table_3.pkl')

# RENAME ROWS AND COLUMNS
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)} 
abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(
 df, 'table_3.tex',
 caption="Elastic Net Model Performance: Mean Square Error", 
 label='table:en_model_performance',
 note="",
 legend=legend)

