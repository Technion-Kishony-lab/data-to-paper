
# IMPORT
import pandas as pd
from typing import Dict, Any, Tuple, Optional
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES

# Define mappings common to all tables
shared_mapping: AbbrToNameDef = {
 'sex': ('Sex', '0: Female, 1: Male'),
 'age_c': ('Age', 'Patient Age in years'),
 'ht': ('Height', 'Patient height in cm'),
 'wt': ('Weight', 'Patient weight in kg'),
 'tube': ('Tube ID', 'Internal diameter of the tube in mm'),
 'tube_depth_G': ('Optimal Tracheal Tube Depth', 'Determined by Chest X-ray in cm')
}

# Table 1:
df1 = pd.read_pickle('table_1.pkl')

# RENAME ROWS AND COLUMNS
mapping1 = {k: v for k, v in shared_mapping.items() if is_str_in_df(df1, k)} 
abbrs_to_names, legend = split_mapping(mapping1)
df1 = df1.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex
to_latex_with_note(
 df1, 'table_1.tex',
 caption="Comparison of mean squared residuals for each Machine Learning Models", 
 label='table:ml_models',
 note="Machine Learning models include Random Forest, Elastic Net, Support Vector Machine and Neural Network.",
 legend=legend)

# Table 2:
df2 = pd.read_pickle('table_2.pkl')

# RENAME ROWS AND COLUMNS
mapping2 = {k: v for k, v in shared_mapping.items() if is_str_in_df(df2, k)} 
mapping2 |= { 'ID Model': ('ID Based Model', 'Optimal Tracheal Tube Depth (in cm) = 3 * Tube ID (in mm)')}
abbrs_to_names, legend = split_mapping(mapping2)
df2 = df2.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex
to_latex_with_note(
 df2, 'table_2.tex',
 caption="Comparison of mean squared residuals for each Formula-Based Models", 
 label='table:formula_models',
 note="Formula-Based models include Height Model, ID Model and Age Model.",
 legend=legend)

# Table 3:
df3 = pd.read_pickle('table_3.pkl')

# FORMAT VALUES
df3['P-value'] = df3['P-value'].apply(format_p_value)

# RENAME ROWS AND COLUMNS
mapping3 = {k: v for k, v in shared_mapping.items() if is_str_in_df(df3, k)} 
abbrs_to_names, legend = split_mapping(mapping3)
df3 = df3.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex
to_latex_with_note(
 df3, 'table_3.tex',
 caption="T-test comparing Machine Learning and Formula-based Models", 
 label='table:comparison',
 note="Statistic and P-value are derived from the t-test.",
 legend=legend)
