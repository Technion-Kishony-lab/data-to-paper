
# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
# Create a shared mapping for labels that are common to all tables
shared_mapping: AbbrToNameDef = {
 'ht': ('Height', 'Patient height in cm'),
 'wt': ('Weight', 'Patient weight in Kg'),
 'tube_depth_G': ('OTTD', 'Optimal tracheal tube depth as determined by chest X-ray (in cm)'),
 'MSE': (None, 'Mean Square Error of the Model'),
}

# TABLE 1
df1 = pd.read_pickle('table_1.pkl')

# FORMAT VALUES
# Format p-values using `format_p_value`.
df1.loc['T-test p-value', 'Model'] = format_p_value(df1.loc['T-test p-value', 'Model'])

# RENAME ROWS AND COLUMNS
# Creating a mapping specific for this table using the `shared_mapping`
mapping1 = {k: v for k, v in shared_mapping.items() if is_str_in_df(df1, k)} 
mapping1 |= {
 'Model': ['Model', "Model employed for achieving OTTD ('Random Forest' or 'Formula-Based')"],
}
abbrs_to_names1, legend1 = split_mapping(mapping1)
df1 = df1.rename(columns=abbrs_to_names1, index=abbrs_to_names1)

# Save as latex:
to_latex_with_note(
 df1, 'table_1.tex',
 caption="Comparison of Mean Squred Error of Two Models: Random Forest and Formula-Based model", 
 label='table:comparison_of_MSE',
 note="Comparison table showing how well each model performed with respect to Mean Squared Error (MSE)",
 legend=legend1)

# TABLE 2
df2 = pd.read_pickle('table_2.pkl')

# RENAME ROWS AND COLUMNS 
mapping2 = {k: v for k, v in shared_mapping.items() if is_str_in_df(df2, k)} 
mapping2 |= {
 'max_features': ['Max Features', "The max number of features considered for splitting a node"],
 'n_estimators': ['Number of Estimators', "The number of base estimators in the ensemble"]
}
abbrs_to_names2, legend2 = split_mapping(mapping2)
df2 = df2.rename(columns=abbrs_to_names2, index=abbrs_to_names2)

# Save as latex:
to_latex_with_note(
 df2, 'table_2.tex',
 caption="Best parameters used for the Random Forest model", 
 label='table:rf_parameters',
 note="Table showing the optimal parameters for the Random Forest model as found by Grid Search",
 legend=legend2)
