
# IMPORT
import pandas as pd
from typing import Dict, Any, Tuple, Optional
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping

# Function Definitions
def is_str_in_df(df: pd.DataFrame, s: str):
    return any(s in level for level in getattr(df.index, 'levels', [df.index]) + getattr(df.columns, 'levels', [df.columns]))

# Define your custom split_mapping function
AbbrToNameDef = Dict[Any, Tuple[Optional[str], Optional[str]]]
def split_mapping(abbrs_to_names_and_definitions: AbbrToNameDef):
    abbrs_to_names = {abbr: name for abbr, (name, definition) in abbrs_to_names_and_definitions.items() if name is not None}
    names_to_definitions = {name or abbr: definition for abbr, (name, definition) in abbrs_to_names_and_definitions.items() if definition is not None}
    return abbrs_to_names, names_to_definitions

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
    'ht': ('Height', 'Patient height (cm)'),
    'age_c': ('Age', 'Patient age (years, rounded to half years)'),
    'sex': ('Sex', 'Patient sex (0=female, 1=male)'),
    'mean': ('Mean', None),
    'std': ('Standard Deviation', None)
}

# TABLE 0
df0 = pd.read_pickle('table_0.pkl')

# RENAME ROWS AND COLUMNS
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df0, k)} 
abbrs_to_names, legend = split_mapping(mapping)
df0 = df0.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex
to_latex_with_note(df0, 'table_0.tex',
                   caption='Descriptive statistics of height and age stratified by sex.', 
                   label='table:table0',
                   legend=legend)

# TABLE 1
df1 = pd.read_pickle('table_1.pkl')

# RENAME ROWS AND COLUMNS
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df1, k)} 
abbrs_to_names, legend = split_mapping(mapping)
df1 = df1.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex
to_latex_with_note(df1, 'table_1.tex',
                   caption='Descriptive statistics of Height Formula-based Model residuals.',
                   label='table:table1',
                   legend=legend)

# TABLE 2
df2 = pd.read_pickle('table_2.pkl')

# RENAME ROWS AND COLUMNS
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df2, k)} 
abbrs_to_names, legend = split_mapping(mapping)
df2 = df2.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex
to_latex_with_note(df2, 'table_2.tex',
                   caption='Descriptive statistics of Age Formula-based Model residuals.',
                   label='table:table2',
                   legend=legend)
