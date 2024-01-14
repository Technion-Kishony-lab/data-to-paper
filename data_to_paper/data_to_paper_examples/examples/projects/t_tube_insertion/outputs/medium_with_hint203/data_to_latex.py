
# IMPORT
import pandas as pd
from typing import Optional, Dict, Any
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
# Shared mapping for labels
shared_mapping: AbbrToNameDef = {
    'tube': ('Tube ID', 'Inner diameter of the tracheal tube (mm)'),
    'sex': ('Sex', '0: Female, 1: Male'),
    'age_c': ('Age (years)', 'Patient age rounded to half years'),
    'ht': ('Height (cm)', "Patient's height in centimeters"),
    'wt': ('Weight (kg)', "Patient's weight in kilograms"),
    'tube_depth_G': ('OTTD (cm)', 'Optimal tracheal tube depth determined by chest X-ray in cm'),
}

# TABLE 1:
df1 = pd.read_pickle('table_1.pkl')

# RENAME ROWS AND COLUMNS
mapping1 = {k: v for k, v in shared_mapping.items() if is_str_in_df(df1, k)} 
mapping1 |= {
 'predicted_formula': ('Predicted OTTD Formula', 'Predicted OTTD using height formula'),
 'residual_formula': ('Residual Formula', 'Residuals of predicted OTTD using height formula'),
}

abbrs_to_names1, legend1 = split_mapping(mapping1)
df1 = df1.rename(columns=abbrs_to_names1, index=abbrs_to_names1)

# Save as latex
to_latex_with_note(df1, 'table_1.tex',
 caption="Summary statistics for observed and predicted OTTDs with height formula-based model", 
 label='table:table1',
 legend=legend1)

# TABLE 2:
df2 = pd.read_pickle('table_2.pkl')

# RENAME ROWS AND COLUMNS
mapping2 = {k: v for k, v in shared_mapping.items() if is_str_in_df(df2, k)} 
mapping2 |= {
    'best_param_n_estimators': ('Best estimators number', 'The optimal number of trees in the forest'),
    'best_param_max_depth': ('Best max depth', 'The best maximum depth of trees'),
    'best_score': ('Best achievable score', 'The highest score achievable on the test set'),
    'RF_model': ('RF Model', 'Random Forest Model'),
}

abbrs_to_names2, legend2 = split_mapping(mapping2)
df2 = df2.rename(columns=abbrs_to_names2, index=abbrs_to_names2)

# Save as latex
to_latex_with_note(df2, 'table_2.tex',
 caption="Optimal parameters and performance of the Random Forest model", 
 label='table:table2',
 legend=legend2)

# TABLE 3:
df3 = pd.read_pickle('table_3.pkl')

# RENAME ROWS AND COLUMNS 
mapping3 = {k: v for k, v in shared_mapping.items() if is_str_in_df(df3, k)}
mapping3 |= {
 't_stat': ('T Statistic', 'T statistic for the difference of means test'),
 'pvalue': ('P-value', 'P value for the difference of means test'),
 'rf_vs_formula': ('RF vs Formula', 'Comparison between Random Forest and Formula-Based models'),
}

# Apply required transformations and formatting
df3['pvalue'] = df3['pvalue'].apply(format_p_value)

abbrs_to_names3, legend3 = split_mapping(mapping3)
df3 = df3.rename(columns=abbrs_to_names3, index=abbrs_to_names3)

# Save as latex
to_latex_with_note(
 df3, 'table_3.tex', 
 caption="Paired T-test between the Squared Residuals of the Machine-Learning Model and the Formula-Based Model", 
 label='table:table3', 
 legend=legend3)
