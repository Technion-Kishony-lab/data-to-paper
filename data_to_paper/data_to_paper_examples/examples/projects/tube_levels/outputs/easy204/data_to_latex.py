
# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef
from typing import Dict, Any, Tuple, Optional

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
 'sex': ('Sex', 'Patient Sex (0 = Female, 1 = Male)'),
 'age_c': ('Age', 'Patient Age (in years, rounded to half years)'),
 'ht': ('Height', 'Patient Height (in cm)'),
 'wt': ('Weight', 'Patient Weight (in kg)'),
}

# TABLE 1
df = pd.read_pickle('table_1.pkl')

# FORMAT VALUES
df['p_value'] = df['p_value'].apply(format_p_value)

# RENAME ROWS AND COLUMNS
column_mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)}
column_mapping.update({
    'p_value': ('P Value', 'the p-value from the t-test'),
    't_statistic': ('T-Statistic', 't-statistic from the t-test'),
})

df = df.rename(columns={k: v[0] for k, v in column_mapping.items() if v[0] is not None})

# Extract definitions to pass to legend
legend = {v[0]: v[1] for k, v in column_mapping.items() if v[1] is not None}

# Save as latex
to_latex_with_note(df, 'table_1.tex',
                   caption="Comparison of predictive performance between Random Forest and Elastic Net Models",
                   label='table:Table_1',
                   legend=legend)
