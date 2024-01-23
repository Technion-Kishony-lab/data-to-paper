
# IMPORT
import pandas as pd
from typing import Dict, Tuple, Optional, List, Any
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
# Preparing a shared mapping for labels common to all tables
shared_mapping: AbbrToNameDef = {
    'ht': ('Height', 'Height in cm'),
    'age_c': ('Age', 'Age in years (rounded to half years)'),
    'sex': ('Sex', '0: Female, 1: Male'),
}
    
# TABLE 0:
df0 = pd.read_pickle('table_0.pkl')

# RENAME ROWS AND COLUMNS
# Preparing mapping for Table 0
mapping0 = {k: v for k, v in shared_mapping.items() if is_str_in_df(df0, k)}
mapping0['mean'] = ('Mean', None)  
mapping0['std'] = ('Standard Deviation', None) 
abbrs_to_names, legend = split_mapping(mapping0)
df0 = df0.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Saving as latex
to_latex_with_note(
    df0, 'table_0.tex',
    caption="Descriptive statistics of Height and Age stratified by Sex", 
    label='table:t0',
    note=None,
    legend=legend)


# TABLE 1:
df1 = pd.read_pickle('table_1.pkl')

# FORMAT VALUES
# format p-value
df1['Paired t-test p value'] = df1['Paired t-test p value'].apply(format_p_value)

# RENAME ROWS AND COLUMNS
# Preparing mapping for Table1
mapping1 = {k: v for k, v in shared_mapping.items() if is_str_in_df(df1, k)}
mapping1['Model'] = (None, None)
mapping1['Mean of Squared Residuals'] = ('Mean Squared Error', None)
mapping1['Paired t-test p value'] = ('p-value', None)
mapping1['Model 1'] = (None, 'Random Forest Model')
mapping1['Model 2'] = (None, 'Formula-based Model')
abbrs_to_names, legend = split_mapping(mapping1)
df1 = df1.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Saving as latex
to_latex_with_note(
    df1, 'table_1.tex',
    caption="Comparison of residuals for Random Forest and Formula-based Models", 
    label='table:t1',
    note=None,
    legend=legend)
