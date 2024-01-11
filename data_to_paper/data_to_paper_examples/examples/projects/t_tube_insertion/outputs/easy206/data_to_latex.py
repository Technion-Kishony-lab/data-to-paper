
# IMPORT
import pandas as pd
from typing import Dict, Any, Tuple, Optional
# Assuming your custom functions are located in 'my_utils.py'
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef 


# PREPARATION FOR ALL TABLES

shared_mapping: AbbrToNameDef = {
 'tube': ('Tube ID', 'Internal diameter of the tube (mm)'),
 'sex': ('Sex', '0: Female, 1: Male'),
 'age_c': ('Age (Circ)', 'Patient age in years, rounded to half years'),
 'ht': ('Height', 'Patient height (cm)'),
 'wt': ('Weight', 'Patient Weight (Kg)'),
 'tube_depth_G': ('Tube Depth G', 'Optimal tracheal tube depth determined by chest X-ray (in cm)')
}

# TABLE 0
df0 = pd.read_pickle('table_0.pkl')

mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df0, k)} 

abbrs_to_names, legend = split_mapping(mapping)
df0 = df0.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(
    df0, 'table_0.tex',
    caption="Descriptive statistics of variables", 
    label='table:descriptive', 
    legend=legend)

# TABLE 1
df1 = pd.read_pickle('table_1.pkl')

# Format p-values
df1['P-value'] = df1['P-value'].apply(format_p_value)

mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df1, k)} 
# Adding Mean Squared Error 
mapping |= {
    'Mean Squared Error': ('MSE', 'Mean Squared Error in Predicting OTTD')
}

abbrs_to_names, legend = split_mapping(mapping)
df1 = df1.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(
    df1, 'table_1.tex',
    caption="Performance of Random Forest (RF) and Elastic Net (EN) models", 
    label='table:performance_en_rf', 
    legend=legend)
