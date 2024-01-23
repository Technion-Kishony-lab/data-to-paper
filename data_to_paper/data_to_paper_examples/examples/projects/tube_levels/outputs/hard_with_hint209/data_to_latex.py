
# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES

shared_mapping: AbbrToNameDef = {
 'MSE': ('Mean Squared Error', 'Mean Squared Error of models'),
 't_stat': ('t-statistic', 'Estimated t-statistics of models'),
 'p_value': ('p-value', 'Estimated p-values of models'),
}

# TABLE 1:
df = pd.read_pickle('table_1.pkl')

# RENAME ROWS AND COLUMNS
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)} 
mapping |= {
 'Random Forest': ('Random Forest', 'Random Forest Regression'),
 'Elastic Net': ('Elastic Net', 'Elastic Net Regression'),
 'Support Vector Machine': ('Support Vector Machine', 'Support Vector Machine Regression'),
 'Neural Network': ('Neural Network', 'Neural Network Regression'),
}

abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# FORMAT VALUES 
df['p-value'] = df['p-value'].apply(format_p_value)

# Save as latex:
to_latex_with_note(
 df, 'table_1.tex',
 caption="Results of Machine Learning Models", 
 label='table:ml_results',
 note="This table presents the results of four machine learning models.",
 legend=legend)
