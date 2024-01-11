
# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
    'tube': ('Tube ID', 'Internal diameter of the tube in mm'),
    'sex': ('Sex', 'Patient sex; 0: Female, 1: Male'),
    'age_c': ('Age (years)', 'Patient age in years, rounded to half years'),
    'ht': ('Height (cm)', 'Patient height in cm'),
    'wt': ('Weight (kg)', 'Patient weight in kg'),
    'tube_depth_G': ('Optimal Tracheal Tube Depth (cm)', 'Optimal tracheal tube depth as determined by chest X-ray in cm'),
    'Model 1': ('Model 1', 'Random Forest Model'),
    'Model 2': ('Model 2', 'Height Formula-based Model'),
    'RMSE': ('RMSE', 'Root Mean Square Error of the model predictions')
}

# TABLE 1
df = pd.read_pickle('table_1.pkl')

# FORMAT VALUES
df['p-value'] = df['p-value'].apply(format_p_value)

# RENAME ROWS AND COLUMNS
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)}
abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(
    df, 'table_1.tex',
    caption="Test of difference in predictive power between formula-based model",
    label='table:prediction_models',
    note="",
    legend=legend
)

# TABLE 2
df = pd.read_pickle('table_2.pkl')

# RENAME ROWS AND COLUMNS
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)}
abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(
    df, 'table_2.tex',
    caption="Root mean square error of formula-based model and the Random Forest model",
    label='table:rmse_models',
    note="",
    legend=legend
)
