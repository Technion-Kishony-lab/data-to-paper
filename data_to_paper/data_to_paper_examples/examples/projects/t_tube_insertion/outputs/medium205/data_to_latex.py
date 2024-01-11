
# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
    'sex': ('Sex', '0: Female, 1: Male'),
    'age_c': ('Age', 'Years, rounded'),
    'ht': ('Height', 'cm'),
    'wt': ('Weight', 'kg'),
    'tube_depth_G mean': ('Tube Mean Depth', 'cm via X-ray'),
    'tube_depth_G std': ('Tube Depth SD', 'cm via X-ray'),
    'age_c mean': ('Mean Age', 'Years, rounded'),
    'age_c std': ('Age SD', 'Years, rounded')}
    
# TABLE 0
df = pd.read_pickle('table_0.pkl')

# FORMATTING VALUES (none required)

# RENAME ROWS and COLUMNS
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)} 
abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Transposition of dataset
df = df.T

# SAVE AS LATEX
to_latex_with_note(
 df,
 'table_0.tex',
 caption='Mean and standard deviation of Optimal Tube Depth based on Sex',
 label='table:table0',
 legend=legend)

# TABLE 1
df = pd.read_pickle('table_1.pkl')

# FORMATTING VALUES 
df['p_val'] = df['p_val'].apply(format_p_value)

# RENAME ROWS and COLUMNS
table_1_mapping = {
    'Height_Formula': ('Height Formula Model', None),
    'RF_model': ('Random Forest Model', None),
    'p_val': ('P-value', None)}
    
mapping = {**shared_mapping, **table_1_mapping}
mapping = {k: v for k, v in mapping.items() if is_str_in_df(df, k)} 

abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# SAVE AS LATEX
to_latex_with_note(
 df,
 'table_1.tex',
 caption='Comparison of residuals between the Machine Learning model and Formula-based model',
 label='table:table1',
 note='The residuals from the ML model and the formula-based model are compared using t-test. The displayed P-value is for the t-test comparison.',
 legend=legend)
