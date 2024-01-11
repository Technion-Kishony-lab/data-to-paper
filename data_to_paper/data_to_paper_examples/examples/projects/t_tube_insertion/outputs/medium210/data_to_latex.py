
# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
 'sex': ('Sex', 'Sex of the patient (0: Female, 1: Male)'),
 'age_c': ('Age', 'Age of the patient in years'),
 'ht': ('Height', 'Height of the patient in cm'),
 'wt': ('Weight', 'Weight of the patient in kg'),
 'tube_depth_G': ('OTTD', 'Optimal Tracheal Tube Depth determined by chest X-ray in cm'),
 'residuals_ML': ('Residuals ML', 'Squared residuals of the machine learning model'),
 'residuals_formula': ('Residuals FBM', 'Squared residuals of the formula-based model'),
 'predicted_ML': ('Predicted ML', 'Predicted OTTD by ML model in cm'),
 'predicted_formula': ('Predicted FBM', 'Predicted OTTD by the formula-based model in cm'),
}

# TABLE 0:
df = pd.read_pickle('table_0.pkl')

# RENAME ROWS AND COLUMNS
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)}
abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as Latex:
to_latex_with_note(
 df, 'table_0.tex',
 caption="Descriptive statistics of Optimal Tracheal Tube Depth (OTTD) stratified by sex",
 label='table:OTTD_Stratified_by_Sex',
 legend=legend)

# TABLE 1:
df = pd.read_pickle('table_1.pkl')

# RENAME ROWS AND COLUMNS
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)} 
abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as Latex:
to_latex_with_note(
 df, 'table_1.tex',
 caption="Predictive performance of the machine-learning model vs the formula-based model",
 label='table:Model_Comparison',
 legend=legend
)
