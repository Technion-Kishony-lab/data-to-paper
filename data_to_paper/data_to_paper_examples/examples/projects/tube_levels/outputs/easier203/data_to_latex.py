
# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef
from typing import Dict, Any, Optional, Tuple

# PREPARATION FOR ALL TABLES
# Shared mapping for labels common to all tables
shared_mapping: AbbrToNameDef = {
    'ht': ('Height (cm)', 'Patient height in cm'),
    'age_c': ('Age (yr)', 'Patient age in years, rounded to half years'),
    'Sex': ('Gender', 'Patient sex, 0: Female, 1: Male')
}

# TABLE 0
df = pd.read_pickle('table_0.pkl')
df = df.T  # Transpose the table

# Rename Rows and Columns
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)}
abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(index=abbrs_to_names)

# Save as Latex
to_latex_with_note(
    df, 'table_0.tex',
    caption="Average and standard deviation of height and age stratified by sex",
    label='table:table_0',
    legend=legend)


# TABLE 1
df = pd.read_pickle('table_1.pkl')
df = df.T  # Transpose the table

# Rename Rows and Columns
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)}
abbreviations = { 
    'Model Residuals' : (None, 'Model Residuals')
}
mapping.update(abbreviations)
abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(index=abbrs_to_names)

# Save as Latex
to_latex_with_note(
    df, 'table_1.tex',
    caption="Mean and standard deviation of residuals",
    label='table:table_1',
    legend=legend)


# TABLE 2
df = pd.read_pickle('table_2.pkl')
df = df.T  # Transpose the table

# Rename Rows and Columns
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)}
abbreviations = { 
    'RMSE' : ('Root Mean Square Error (RMSE)', None)
}
mapping.update(abbreviations)
abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(index=abbrs_to_names)

# Save as Latex
to_latex_with_note(
    df, 'table_2.tex',
    caption="Root Mean Square Error (RMSE) of the models",
    label='table:table_2',
    legend=legend)


# TABLE 3
df = pd.read_pickle('table_3.pkl')
# Format p-values before the transpose operation
df['p-value'] = df['p-value'].apply(format_p_value)
df = df.T  # Transpose the table

# Rename Rows and Columns
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)}
abbreviations = { 
    't-value' : ('T-statistic', None),
    'p-value' : ('P-value', None)
}
mapping.update(abbreviations)
abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(index=abbrs_to_names)

# Save as Latex
to_latex_with_note(
    df, 'table_3.tex',
    caption="Paired t-Test Residuals",
    label='table:table_3',
    legend=legend)
