
# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
    'ML Mean Sq Residual': ('ML MSE', 'Mean Squared Error of Machine-Learning models'),
    'Formula Mean Sq Residual': ('Formula MSE', 'Mean Squared Error of Formula-based models'),
    'p-value': ('p-value', 'p-value from the paired t-test comparing ML models with formula-based models'),
}

# TABLE 1:
df1 = pd.read_pickle('table_1.pkl')

# RENAME ROWS AND COLUMNS
# Shorten the row names: replace '_' with ' ' and make abbreviations for formula names
df1 = df1.rename(index=lambda x: x.replace("_", " ").replace(" vs height formula", " vs Height").replace(" vs age formula", " vs Age").replace(" vs id formula", " vs ID"))

# Use shared_mapping
mapping1 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df1, k))

abbrs_to_names1, legend1 = split_mapping(mapping1)
df1 = df1.rename(columns=abbrs_to_names1, index=abbrs_to_names1)

# SAVE AS LATEX:
to_latex_with_note(
    df1, 'table_1.tex',
    caption="Comparison of mean squared residuals of predicted OTTD by various models.", 
    label='table:comparison',
    note=None,
    legend=legend1)
