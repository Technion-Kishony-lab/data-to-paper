
# IMPORT
import pandas as pd
from typing import Dict, Optional, Any, Tuple
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping
from my_utils import AbbrToNameDef

# PREPARATION FOR ALL TABLES
SharedMapping: AbbrToNameDef = {
    'sex': ('Sex', '0: Female, 1: Male'),
    'age_c': ('Age (years)', None),
    'ht': ('Height (cm)', None),
    'wt': ('Weight (kg)', None),
    'tube_depth_G': ('OTTD (cm)', 'Optimal tracheal tube depth, as determined by chest X-ray')
}

# TABLE 0
df = pd.read_pickle('table_0.pkl')

# RENAME ROWS AND COLUMNS
mapping = {k: v for k, v in SharedMapping.items() if is_str_in_df(df, k)}
mapping.update({
    'age_c': ('Age (years)', 'Average age rounded to half years'),
    'ht': ('Height (cm)', 'Average height'),
})

abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, level=0)

# Save as latex:
to_latex_with_note(
 df, 
 'table_0.tex', 
 caption="Descriptive statistics of height and age stratified by sex", 
 label='table:statistics',
 legend=legend)

# TABLE 1
df = pd.read_pickle('table_1.pkl')

# FORMAT P-VALUES
df['p-value'] = df['p-value'].apply(format_p_value)

# RENAME ROWS AND COLUMNS
mapping = {
    'Average Squared Residual': ('Average Squared Residual', None),
    'p-value': ('P-value', None),
    'Random Forest': ('Random Forest Model', None),
    'Height-based model': ('Height-based formula model', None),
}

abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(
    df, 
    'table_1.tex', 
    caption="Comparison of Random Forest model with Height-based model for predicting the optimal tracheal tube depth (OTTD)", 
    label='table:comparison',
    legend=legend)

