
# IMPORT
import pandas as pd
from typing import Any, Dict, Tuple, Optional
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES

shared_mapping: AbbrToNameDef = {
 'mean': ('Mean OTTD', 'Mean Optimal Tracheal Tube Depth (cm)'),
 'std': ('Standard Deviation', 'Standard Deviation of OTTD (cm)'),
 'mse': ('Mean Squared Error', 'Mean Squared Error of the model'),
 'p_value': ('P-value', 'Wilcoxon test p-value of model residuals'),
 'sex': ('Sex', 'Gender of patient 0: Female, 1: Male'),
 'age_c': ('Age', 'Age of patient in years'),
 'ht': ('Height', 'Height of patient in cm'),
 'wt': ('Weight', 'Weight of patient in kgs'),
 'tube_depth_G': ("Observed OTTD", "Optimal Tracheal Tube Depth as determined by chest X-ray (cm)"),
 'mean_residual': ('Mean Residual', 'Mean Residual of the model')
}

# TABLE 0:

df = pd.read_pickle('table_0.pkl')

mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)} 
abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(
 df, 'table_0.tex',
 caption='Descriptive statistics of Optimal Tracheal Tube Depth (OTTD) stratified by sex', 
 label='table:statistics_by_sex',
 note=None,
 legend=legend)

# TABLE 1:

df = pd.read_pickle('table_1.pkl')

model_mapping: AbbrToNameDef = {
 'Model 1': ('Random Forest Model', None),
 'Model 2': ('Formula-Based Model', None)
}

mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)} 
mapping |= model_mapping
abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(
 df, 'table_1.tex',
 caption='Performance comparison between Machine-Learning model and Formula-Based model', 
 label='table:performance_model',
 note=None,
 legend=legend)

# TABLE 2:

df = pd.read_pickle('table_2.pkl')

mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)} 
mapping |= model_mapping
abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Format P-values
df['P-value'] = df['P-value'].apply(format_p_value)

# Save as latex:
to_latex_with_note(
 df, 'table_2.tex',
 caption='Comparison of model residuals (prediction - target) between Random Forest model and Formula-Based model', 
 label='table:comparison_model',
 note=None,
 legend=legend)
