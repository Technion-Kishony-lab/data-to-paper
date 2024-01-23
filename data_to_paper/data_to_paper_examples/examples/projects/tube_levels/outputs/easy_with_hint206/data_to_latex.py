
# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
# Define a shared mapping for labels that are common to all tables.
shared_mapping: AbbrToNameDef = {
 'sex': ('Sex', '0: Female, 1: Male'),
 'age_c_scaled': ('Age (Scaled)', 'Patient age in years, rounded to half years, scaled'),
 'ht_scaled': ('Height (Scaled)', 'Patient height in cm, scaled'),
 'wt_scaled': ('Weight (Scaled)', 'Patient weight in kg, scaled'),
 'tube_depth_G': ('Optimal Tube Depth', 'Optimal tracheal tube depth as determined by chest X-ray (in cm), G stands for gold-standard')
}

# TABLE 1:
df = pd.read_pickle('table_1.pkl')

# FORMAT VALUES
# Format p-value
df['p-value'] = df['p-value'].apply(format_p_value)

# RENAME ROWS AND COLUMNS
# Rename any abbreviated or not self-explanatory table labels to scientifically-suitable names.
# Use the shared_mapping
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)} 
mapping.update({
 'Model': ('Model', 'Machine learning model used for prediction'), 
 'Mean Squared Error': ('Mean Squared Error', 'The average of the squares of the differences between predicted and actual values'), 
 't-value': ('t-value', 'The calculated difference represented in units of standard error'),
 'p-value': ('p-value', 'The probability of obtaining the observed data given that the null hypothesis is true')
}) 
abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Update legend to add the explanation of row labels 'Model 1' and 'Model 2'
legend.update({
 'Model 1': 'Random Forest Model',
 'Model 2': 'Elastic Net Model'
})

# Save as latex:
to_latex_with_note(
 df, 'table_1.tex',
 caption="Comparison of Mean Squared Errors of the Models", 
 label='table:comparison_models',
 note="This table compares the performance of the Random Forest and Elastic Net models in predicting the optimal tracheal tube depth.",
 legend=legend
)
