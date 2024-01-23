
# IMPORT
import pandas as pd
from typing import Dict, Any, Tuple, Optional
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
 'sex': ('Sex', 'Participant sex: 0 - Female, 1 - Male'),
 'age_c': ('Age (years)', 'Patient age in years. Rounded to half years.'),
 'ht': ('Height (cm)', 'Patient height in centimeters.'),
 'wt': ('Weight (kg)', 'Patient weight in kilograms.'),
 'tube_depth_G': ('Optimal Tube Depth (cm)', 'Optimal tracheal tube depth as determined by Chest X-ray (in cm).')
}

# TABLE 0
df = pd.read_pickle('table_0.pkl')

# RENAME ROWS AND COLUMNS 
mapping: AbbrToNameDef = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)} 

abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex
to_latex_with_note(
 df, 'table_0.tex',
 caption="Descriptive Statistics of Patient's Sex, Age, Height, Weight and Optimal Tracheal Tube Depth.", 
 label='table:descriptive_statistics',
 legend=legend)

# TABLE 1
df = pd.read_pickle('table_1.pkl')

# Format the DataFrame and p-values
df.rename(columns={col: col.replace('_', ' ') for col in df.columns}, inplace=True)
df.rename(columns={
    'Squared Residues': 'SR',
    'p-value vs Height Formula': 'p-val HF',
    'p-value vs Age Formula': 'p-val AF',
    'p-value vs ID Formula': 'p-val IDF'
    }, inplace=True)

for col in df.columns:
    if 'p-val' in col:
        df[col] = df[col].apply(format_p_value)

# RENAME ROWS AND COLUMNS 
mapping: AbbrToNameDef = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)} 
mapping |= {
    'SR': ('SR', 'Squared Residues of the model predictions.'),
    'p-val AF': ('p-val AF', 'p-value of the Age Formula-Based Model.'),
    'p-val HF': ('p-val HF', 'p-value of the Height Formula-Based Model.'),
    'p-val IDF': ('p-val IDF', 'p-value of the ID Formula-Based Model.'),
    'ID Formula': ('ID Formula', 'OTTD (in cm) = 3 * (tube ID [mm])')
}

abbrs_to_names, legend = split_mapping(mapping)
df.rename(index=abbrs_to_names, inplace=True)

# Save as latex
to_latex_with_note(
 df, 'table_1.tex',
 caption="Performance comparison among Machine Learning models and formula-based models", 
 label='table:performance_comparison',
 legend=legend)

