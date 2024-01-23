
# IMPORT
import pandas as pd
from typing import Dict, Any, Tuple, Optional
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
}

# TABLE 1
df = pd.read_pickle('table_1.pkl')

# FORMAT VALUES
df['p_value'] = df['p_value'].apply(format_p_value)

# RENAME ROWS AND COLUMNS
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)} 
mapping |= {
 'Mean_Squared_Residuals': ('Mean Squared Residuals', 'Squared residuals (prediction - target)**2'),
 't_statistic': ('t-statistic', 'Statistical t value'),
 'p_value': ('p-value', 'Two-tailed p value for hypothesis test'),
 'RFM': ('Random Forest Model', None),
 'HFMB': ('Height Formula-Based Model', None)
}

abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(
 df, 'table_1.tex',
 caption="Performance comparison of Random Forest Model (RFM) and Height Formula-Based Model (HFMB)", 
 label='table:rf_hfmb_comparison',
 note=None,
 legend=legend)

# TABLE 2
df = pd.read_pickle('table_2.pkl')

# RENAME ROWS AND COLUMNS
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)}
mapping |= {
 'Importance': ('Importance', 'Feature importance as computed by the Random Forest model'),
 'sex': ('Sex', 'Patient sex (0=female, 1=male)'),
 'age_c': ('Age', "Patient's age in years"),
 'ht': ('Height', "Patient's height in cm"),
 'wt': ('Weight', "Patient's weight in kg")
}

abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(
 df, 'table_2.tex',
 caption="Feature Importance of Random Forest Model (RFM)", 
 label='table:rfm_feature_importance',
 note=None,
 legend=legend)
