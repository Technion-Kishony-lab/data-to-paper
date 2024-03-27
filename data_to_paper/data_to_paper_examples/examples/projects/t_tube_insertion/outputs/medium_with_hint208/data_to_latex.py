
# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping
from typing import Dict, Any, Tuple, Optional

AbbrToNameDef = Dict[Any, Tuple[Optional[str], Optional[str]]]

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
    'tube_depth_G': ('OTTD', 'Optimal Tracheal Tube Depth determined by chest X-ray (cm)'),
    'sex': ('Sex', '1: male, 0: female'),
    'age_c': ('Age', 'Age of the patient (in years)'),
    'ht': ('Height', 'Height of the patient (in cm)'),
    'wt': ('Weight', 'Weight of the patient (in kg)'),
    'tube': ('Tube Diameter', 'Internal diameter of the tube in mm used for mechanical ventilation')
}

# TABLE 0:
df = pd.read_pickle('table_0.pkl')

# RENAME ROWS AND COLUMNS
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)}
abbrs_to_names, names_to_definitions = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(
 df, 'table_0.tex',
 caption="Descriptive statistics of OTTD stratified by sex", 
 label='table:table_0',
 note="mean: Average Value\nstd: Standard Deviation",
 legend=names_to_definitions
)

# TABLE 1:
df = pd.read_pickle('table_1.pkl')

# RENAME ROWS AND COLUMNS
Mapping = {
    'Model': (None, 'Predictive Model Name'),
    'Residuals Mean Squared Error': ('Residuals MSE', 'Mean Squared Error of residuals'),
    'T-statistic': ('T-Statistic', 'Value of T-Statistic for paired T-test involving residuals'),
    'P-value': ('P-Value', 'Corresponding P-Value for the test statistic')
}
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)}
mapping.update(Mapping)
abbrs_to_names, names_to_definitions = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# FORMAT VALUES
df['P-Value'] = df['P-Value'].apply(format_p_value)

# Save as latex:
to_latex_with_note(
 df, 'table_1.tex',
 caption="Model performance comparison: Random Forest vs. Height-based Formula", 
 label='table:table_1',
 note="Index\n1. Random Forest\n2. Height-based Formula",
 legend=names_to_definitions
)
