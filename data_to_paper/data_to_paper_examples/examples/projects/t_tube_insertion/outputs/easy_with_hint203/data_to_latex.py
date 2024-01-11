
# IMPORT
import pandas as pd
from typing import Dict, Optional, Tuple

# MODIFY THE IMPORT ACCORDING TO YOUR ACTUAL DIRECTORY OF FUNCTIONS
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES

shared_mapping: AbbrToNameDef = {
 'sex': ('Sex', '0: Female, 1: Male'),
 'age_c': ('Age', 'Age in Years'),
 'ht': ('Height', 'Height in cm'),
 'wt': ('Weight', 'Weight in kg'),
 'tube_depth_G': ('OTTD', 'Optimal Tracheal Tube Depth as determined by chest X-ray (in cm)'),
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
 caption="Descriptive statistics of Height and Age stratified by Sex", 
 label='table:Descriptive_statistics',
 note=None,
 legend=legend)


# TABLE 1
df = pd.read_pickle('table_1.pkl')

# FORMAT VALUES 
df['p-value'] = df['p-value'].apply(format_p_value)

mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)}
mapping |= {
 'Mean Squared Residuals': ('Mean Sq. Residuals', None),
 'STD of Squared Residuals': ('STD Sq. Residuals', None),
 'p-value': ('P-value', 'P-value of the hypothesis that the two models have different predictive powers.'),
 'RF': ('Random Forest', 'Random Forest model'),
 'EN': ('Elastic Net', 'Elastic Net model'),
}

abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(
 df, 'table_1.tex',
 caption="Comparison of predictive performance of two models", 
 label='table:Comparison_predictive_performance',
 note=None,
 legend=legend)
