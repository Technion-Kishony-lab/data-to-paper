

# IMPORT
import pandas as pd
from typing import Dict, Tuple, Optional, Any
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
 'tube': ('Tube ID', 'Internal diameter of the tube (mm)'),
 'sex': ('Sex', 'Patient sex (0 = Female, 1 = Male)'),
 'age_c': ('Age', 'Patient age (years, rounded to half years)'),
 'ht': ('Height', 'Patient height (cm)'),
 'wt': ('Weight', 'Patient weight (kg)'),
 'tube_depth_G': ('O.T.T.D', 'Optimal tracheal tube depth as determined by chest X-ray (cm)')
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
 caption="Descriptive statistics of the dataset", 
 label='table:desc_stats',
 note=None,
 legend=legend)

# TABLE 1
df = pd.read_pickle('table_1.pkl')

# RENAME ROWS AND COLUMNS
mapping = {
 'Mean Squared Error': ('MSE', 'Mean Squared Error - a performance metric for machine learning models'),
}

abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex
to_latex_with_note(
 df, 'table_1.tex',
 caption="Performance metrics for different machine learning models", 
 label='table:machine_learning_performance',
 note="The table presents the Mean Squared Error (MSE) for each machine learning model.",
 legend=legend)

# TABLE 2
df = pd.read_pickle('table_2.pkl')

# RENAME ROWS AND COLUMNS
mapping = {
 'Mean Squared Error': ('MSE', 'Mean Squared Error - a performance metric for formula-based models'),
 'Height Model': ('Height Model', 'OTTD = height [cm] / 10 + 5 cm'),
 'Age Model': ('Age Model', 'OTTD per age category: 0 <= age [years] < 0.5: 9cm, 0.5 <= age [years] < 1: 10cm, 1 < age [years] < 2: 11cm, 2 < age [years]: 12cm + (age [years]) * 0.5 cm / year'),
 'ID Model': ('Tube Diameter Model', 'OTTD (in cm) = 3 * (tube ID [mm]) * cm/mm')
}

abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex
to_latex_with_note(
 df, 'table_2.tex',
 caption="Performance metrics for different formula-based models", 
 label='table:formula_based_performance',
 note="The table presents the Mean Squared Error (MSE) for each formula-based model.",
 legend=legend)

