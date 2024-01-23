
# IMPORT
import pandas as pd
from typing import Optional, Dict
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
 'sex': ('Sex', 'Participant gender, 0: Female, 1: Male'),
 'age_c': ('Age', 'Participant age in years, rounded to half years'),
 'ht': ('Height', 'Participant height in cm'),
 'wt': ('Weight', 'Participant weight in kg'),
}

# TABLE 1:
df = pd.read_pickle('table_1.pkl')

# RENAME ROWS AND COLUMNS 
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)} 
mapping |= {
 'Mean Squared Residual': ('Mean Squared Residual (cm squared)', 'Average of squared differences between predicted and actual OTTD (in cm^2) '),
 'Standard Error': ('Standard Error (cm)', 'Standard error of the mean squared residuals (in cm)'),
}
abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(
 df, 'table_1.tex',
 caption="Comparison of Mean Squared Residuals between Machine Learning Model and Formula-based Model", 
 label='table:comparison',
 note=None,
 legend=legend)

# TABLE 2:
df = pd.read_pickle('table_2.pkl')

# RENAME ROWS AND COLUMNS 
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)} 
mapping |= {
 'Importance': ('Importance', 'Relative importance of each feature in the Random Forest model'),
}
abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(
 df, 'table_2.tex',
 caption="Feature Importances in Random Forest Model", 
 label='table:importance',
 note=None,
 legend=legend)
 
