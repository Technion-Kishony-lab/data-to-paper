
# IMPORT
import pandas as pd
from typing import Dict, Any, Optional, Tuple
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
 'sex': ('Sex', 'Patient sex (0=female, 1=male)'),
 'age_c': ('Age', 'patient age in years, rounded to half years'),
 'ht': ('Height', 'Patient height in cm'),
 'wt': ('Weight', 'Patient weight in kg'),
 'tube_depth_G': ('OTTD', 'Optimal tracheal tube depth as determined by chest X-ray (in cm)'),
 'Mean Squared Error': ('MSE', 'Mean Squared Error of the model predictions'),
 'T-test P-value': ('T-test P-value', 'P-value of the paired t-test comparing the squared residuals of the 2 models'),
 'R Squared Score': ('R Squared Score', 'Coefficient of determination of the model predictions'),
 'RMSE': ('RMSE', 'Root Mean Squared Error of the model predictions')
}

# TABLE 1:
df1 = pd.read_pickle('table_1.pkl')

# FORMAT VALUES 
df1['T-test P-value'] = df1['T-test P-value'].apply(format_p_value)

# RENAME ROWS AND COLUMNS
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df1, k)}
abbrs_to_names, legend = split_mapping(mapping)
df1 = df1.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(
    df1, 'table_1.tex',
    caption = "Comparison of Random Forest and Elastic Net model performance in predicting OTTD after hyperparameter tuning.",
    label = 'table:comparison_models',
    note = None,
    legend = legend
)

# TABLE 2:
df2 = pd.read_pickle('table_2.pkl')

# RENAME ROWS AND COLUMNS
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df2, k)}
abbrs_to_names, legend = split_mapping(mapping)
df2 = df2.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as Latex:
to_latex_with_note(
    df2, 'table_2.tex',
    caption = "R squared score for Random Forest and Elastic Net models in predicting OTTD.",
    label = 'table:r_squared',
    note = None,
    legend = legend
)

# TABLE 3:
df3 = pd.read_pickle('table_3.pkl')

# RENAME ROWS AND COLUMNS
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df3, k)}
abbrs_to_names, legend = split_mapping(mapping)
df3 = df3.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as Latex:
to_latex_with_note(
    df3, 'table_3.tex',
    caption = "Root Mean Squared Error for Random Forest and Elastic Net models in predicting OTTD.",
    label = 'table:root_mse',
    note = None,
    legend = legend
)
