
# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping
from typing import Dict

# PREPARATION FOR ALL TABLES
# Define mapping shared by all tables
shared_mapping = {
 'tube_depth_G': ('OTTD', 'Optimal tracheal tube depth as determined by chest X-ray (in cm)'),
 'ML_model_MSE': ('MLE', 'Mean Squared error of Machine Learning Model'),
 'formula_model_MSE': ('FormMLE', 'Mean Squared error of Formula Model'),
 'Paired_ttest_pval': ('P-Value', 'P-Value from Paired t-test'),
 }

# TABLE 1:
# Load the Data
df1 = pd.read_pickle('table_1.pkl')

# Apply shared_mapping specific to table1
mapping_table1 = {k: v for k, v in shared_mapping.items() if is_str_in_df(df1, k)} 

# Split mapping to names and definitions
abbrs_to_names, names_to_definitions = split_mapping(mapping_table1)

# Renaming columns
df1.rename(columns = abbrs_to_names, inplace=True)

# Format p-value columns
df1['P-Value'] = df1['P-Value'].apply(format_p_value)

# Save as latex:
to_latex_with_note(
    df1,
    'table_1.tex',
    caption="Mean squared errors of ML model and formula-based model, and p-value from paired t-test",
    label='table:table_1',
    note=None,
    legend=names_to_definitions)
