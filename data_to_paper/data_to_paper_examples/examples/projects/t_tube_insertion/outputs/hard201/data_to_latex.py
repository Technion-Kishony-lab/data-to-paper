
# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES

# shared mappings for labels common to the two tables.
shared_mapping: AbbrToNameDef = {
 'Error': ('MSR', 'Mean Squared Residuals: i.e., The average of the squared errors from the predicted optimal tracheal tube depth.'),
}

# TABLE 1
df = pd.read_pickle('table_1.pkl')

# RENAME ROWS AND COLUMNS
# Rename abbreviated or not self-explanatory table labels to scientifically-suitable names.
# make a copy of shared_mapping for table1
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)}
mapping |= {
    'Random Forest': ('RF', 'Random Forest algorithm'),
    'Elastic Net': ('EN', 'Elastic Net'),
    'Support Vector Machine': ('SVM', 'Support Vector Machine algorithm'),
    'Neural Network': ('NN', 'Neural Network algorithm'),
    'Height Formula': ('HF', 'Height Formula-based Model'),
    'Age Formula': ('AF', 'Age Formula-based Model'),
    'ID Formula': ('IDF', 'ID Formula-based Model')
}
abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(
 df, 'table_1.tex',
 caption="Comparison of Mean Squared Residuals between Machine Learning and Formula-based Models", 
 label='table:msr_comparison',
 legend=legend)

# TABLE 2
df = pd.read_pickle('table_2.pkl')

# FORMAT VALUES
# Format P-values with `format_p_value`.
for col in df.columns:
    df[col] = df[col].apply(format_p_value)

mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)}
mapping |= {
 'Height Formula p-value': ('HFpv', 'Significance (p-value) of Height Model compared to ML models'),
 'Age Formula p-value': ('AFpv', 'Significance (p-value) of Age Model compared to ML models'),
 'ID Formula p-value': ('IDFpv', 'Significance (p-value) of ID Model compared to ML models')
}

abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(
 df, 'table_2.tex',
 caption="Significance (p-value) in Prediction Errors between Machine Learning Models and Formula-based Models", 
 label='table:pv_comparison',
 legend=legend)
