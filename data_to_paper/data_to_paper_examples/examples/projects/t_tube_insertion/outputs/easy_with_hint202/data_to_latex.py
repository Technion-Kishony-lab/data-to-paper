
# IMPORT
import pandas as pd
from typing import Dict, Any, Tuple, Optional
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping

# PREPARATION FOR ALL TABLES
shared_mapping: Dict[str, Tuple[Optional[str], Optional[str]]] = {
 'sex': ('Sex', 'Patient sex (0 for female, 1 for male)'),
 'age_c': ('Age', 'Patient age (in years)'),
 'ht': ('Height', 'Patient height (in cm)'),
 'wt': ('Weight', 'Patient weight (in kg)'),
 'tube': ('Tube ID', 'Internal diameter of the tube (in mm)'),
 'tube_depth_G': ('Optimal Tracheal Tube Depth (OTTD)', 'As determined by chest X-ray (in cm)'),
}

# TABLE 0
df = pd.read_pickle('table_0.pkl')

# RENAME ROWS AND COLUMNS
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)}
abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex
to_latex_with_note(
 df, 'table_0.tex',
 caption="Descriptive statistics of patient features and OTTD stratified by sex", 
 label='table:patient_features_ottd_by_sex',
 legend=legend)

# TABLE 1
df = pd.read_pickle('table_1.pkl')

# RENAME ROWS AND COLUMNS
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)}
abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex
to_latex_with_note(
 df, 'table_1.tex',
 caption="Performance of Random Forest and Elastic Net models in predicting OTTD", 
 label='table:model_performance',
 legend=legend)

# TABLE 2
df = pd.read_pickle('table_2.pkl')

# FORMAT VALUES
df['p value'] = df['p value'].apply(format_p_value)

# RENAME ROWS AND COLUMNS
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)}
abbrs_to_names, legend = split_mapping(mapping)
df.rename(columns=abbrs_to_names, index=abbrs_to_names, inplace=True)

# Save as latex
to_latex_with_note(
 df, 'table_2.tex',
 caption="Paired t-test comparing the squared residuals of the two models", 
 label='table:paired_ttest',
 legend=legend)
