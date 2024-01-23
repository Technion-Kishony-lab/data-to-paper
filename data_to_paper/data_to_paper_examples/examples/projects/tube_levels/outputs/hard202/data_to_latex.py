
# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping
from typing import Dict, Any, Optional, Tuple

# PREPARATION FOR ALL TABLES
shared_mapping = {
    'tube': ('Tube ID', 'Internal diameter of the tube (mm)'),
    'age_c': ('Age', 'Patient age (years, rounded to half years)'),
    'ht': ('Height', 'Patient height (cm)'),
    'wt': ('Weight', 'Patient weight (kg)'),
    'tube_depth_G': ('OTTD', 'Optimal Tracheal Tube Depth as determined by chest X-ray (in cm)'),
}

# TABLE 0:
df0 = pd.read_pickle('table_0.pkl')

# RENAME ROWS AND COLUMNS
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df0, k)}

# Here, we specify the labels for male and female as given in the description of the dataset
mapping.setdefault('female', ('Female', None)) 
mapping.setdefault('male', ('Male', None)) 
abbrs_to_names, legend = split_mapping(mapping)
df0.rename(columns=abbrs_to_names, index=abbrs_to_names, inplace=True)

# Save as latex:
to_latex_with_note(
 df0, 'table_0.tex',
 caption="Descriptive statistics of Tube ID and OTTD stratified by sex", 
 label='table:descriptive_statistics',
 note=None,
 legend=legend)

# TABLE 1:
df1 = pd.read_pickle('table_1.pkl')

# FORMAT VALUES
df1['p-value'] = df1['p-value'].apply(format_p_value)

# RENAME ROWS 
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df1, k)} 
abbrs_to_names, legend = split_mapping(mapping)
df1.rename(index=abbrs_to_names, inplace=True)

# Save as latex:
to_latex_with_note(
 df1, 'table_1.tex',
 caption="Comparison of Residual Sums of Squares (RSS) of each model", 
 label='table:model_comparison',
 note=None,
 legend=legend)
