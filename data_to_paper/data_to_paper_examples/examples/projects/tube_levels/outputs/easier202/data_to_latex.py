
# IMPORT
import pandas as pd
from typing import Optional, Dict, List, Union, Tuple
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES

# As applicable, define the mapping for labels that are common to all tables
shared_mapping: AbbrToNameDef = {
 'sex': ('Sex', '0: Female, 1: Male'),
 'age_c': ('Age (years)', None),
 'ht': ('Height (cm)', None),
 'tube_depth_G': ('Measured OTTD (cm)', 'Optimal Tracheal Tube Depth, as measured by chest X-ray'),
}

# TABLE 0:
df = pd.read_pickle('table_0.pkl')

# FORMAT VALUES

# RENAME ROWS AND COLUMNS
# Rename any abbreviated or not self-explanatory table labels to scientifically-suitable names
# Use the 'shared_mapping' 
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)} 
mapping.update({
 'mean_ht': ('Avg. Height (cm)', 'Mean height of the patients'),
 'mean_age_c': ('Avg. Age (years)', 'Mean age of the patients'),
 'std_ht': ('Height Std. Dev.', 'Standard deviation of height'),
 'std_age_c': ('Age Std. Dev.', 'Standard deviation of age'),
})
abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(
 df, 'table_0.tex',
 caption="Descriptive statistics of height and age stratified by sex", 
 label='table:descriptive_statistics',
 note="Table presents the mean and standard deviation of height and age, stratified by sex",
 legend=legend)

# TABLE 1:
df1 = pd.read_pickle('table_1.pkl')

# FORMAT VALUES

# RENAME ROWS AND COLUMNS
# Rename any abbreviated or not self-explanatory table labels to scientifically-suitable names
# Use the 'shared_mapping' 
mapping1 = {k: v for k, v in shared_mapping.items() if is_str_in_df(df1, k)} 
mapping1.update({
 'Height model': ('Height-based OTTD (cm)', 'Optimal Tracheal Tube Depth predicted by the Height-based formula model'),
 'Age model': ('Age-based OTTD (cm)', 'Optimal Tracheal Tube Depth predicted by the Age-based formula model'),
})

abbrs_to_names1, legend1 = split_mapping(mapping1)
df1 = df1.rename(columns=abbrs_to_names1, index=abbrs_to_names1)

# Save as latex:
to_latex_with_note(
 df1, 'table_1.tex',
 caption="Comparison of actual OTTD measurements and predictions from the height and age models", 
 label='table:comparison_ottd_models',
 note="Table presents the mean squared residuals between the actual and predicted Optimal Tracheal Tube Depth, as predicted by the two formula-based models",
 legend=legend1)
 