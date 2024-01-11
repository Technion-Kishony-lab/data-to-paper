
# IMPORT
import pandas as pd
from typing import Dict, Any, Optional, Tuple
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
    'Mean Squared Error': ('MSE', 'Mean Squared Error, value closer to zero is better'),
    'SVM': ('Support Vector Machine', None),
    'Random Forest': ('Random Forest Regressor', None),
    'Elastic Net': ('Elastic Net Regressor', None),
    'ID': ('Tube ID', 'internal diameter of the tracheal tube in millimeter'),
    'Height': ('Patient Height', 'Height of the patient in cm'),
    'Age': ('Patient Age', 'Age of the patient in years')
}

# TABLE 1:
df1 = pd.read_pickle('table_1.pkl')

# RENAME ROWS AND COLUMNS
mapping1 = {k: v for k, v in shared_mapping.items() if is_str_in_df(df1, k)}
abbrs_to_names1, legend1 = split_mapping(mapping1)
df1 = df1.rename(columns=abbrs_to_names1, index=abbrs_to_names1)

# Save as latex
to_latex_with_note(
    df1, 'table_1.tex',
    caption="Mean Squared Error for each Machine Learning Model",
    label='table:ml_mse',
    note="Machine Learning Models include: Random Forest, Elastic Net, Support Vector Machine, Neural Network",
    legend=legend1)


# TABLE 2:
df2 = pd.read_pickle('table_2.pkl')

# RENAME ROWS AND COLUMNS
mapping2 = {k: v for k, v in shared_mapping.items() if is_str_in_df(df2, k)}
abbrs_to_names2, legend2 = split_mapping(mapping2)
df2 = df2.rename(columns=abbrs_to_names2, index=abbrs_to_names2)

# Save as latex
to_latex_with_note(
    df2, 'table_2.tex',
    caption="Mean Squared Error for each Formula-Based Model",
    label='table:formula_mse',
    note="Formula-Based Models include: ID (Tube ID Model), Height (Height Formula Model), Age (Age Formula Model)",
    legend=legend2)


# TABLE 3:
df3 = pd.read_pickle('table_3.pkl')

# FORMAT P-VALUES
df3 = df3.applymap(format_p_value)

# SAVE AS LATEX
to_latex_with_note(
    df3, 'table_3.tex',
    caption="Paired T-Test Comparison between Machine Learning and Formula-Based Model Predictions",
    label='table:p_values',
    note="P-values formatted to be less than 1e-06 if it's less than 1e-06")

