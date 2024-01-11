

# IMPORT
import pandas as pd
from typing import Dict, Any, Tuple, Optional
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
# Let's keep the shared mapping empty since these labels are not shared across the tables.
shared_mapping: AbbrToNameDef = {}

# TABLE 1:

# read table 1 data
df = pd.read_pickle('table_1.pkl')

# Prepare specific labels and definitions for table 1
table_1_specific_mapping: AbbrToNameDef = {
    'RF': ('RF', 'Random Forest model'),
}

# Merge shared mapping and specific mapping
mapping = {**shared_mapping, **table_1_specific_mapping}
abbrs_to_names, names_to_definitions = split_mapping(mapping)

# Rename columns and save as a LaTeX table
df = df.rename(columns=abbrs_to_names)
to_latex_with_note(df, 'table_1.tex', caption='Performance of the Random Forest Model', 
                   label='table:RF_Performance', note=None, legend=names_to_definitions)


# TABLE 2:

# read table 2 data
df = pd.read_pickle('table_2.pkl')

# Prepare specific labels and definitions for table 2
table_2_specific_mapping: AbbrToNameDef = {
    'EN': ('EN', 'Elastic Net model'),
}

# Merge shared mapping and specific mapping
mapping = {**shared_mapping, **table_2_specific_mapping}
abbrs_to_names, names_to_definitions = split_mapping(mapping)

# Rename columns and save as a LaTeX table
df = df.rename(columns=abbrs_to_names)
to_latex_with_note(df, 'table_2.tex', caption='Performance of the Elastic Net Model', 
                   label='table:EN_Performance', note=None, legend=names_to_definitions)


# TABLE 3:

# read table 3 data
df = pd.read_pickle('table_3.pkl')

# Prepare specific labels and definitions for table 3
table_3_specific_mapping: AbbrToNameDef = {
    'Model Pair': ('Compared Models', 'Pair of models compared'),
    't-statistic': ('t-statistic', 'Statistical measure for the Hypothesis Test'),
    'p-value': ('p-value', 'Significance measure for the Hypothesis Test'),
}

# Merge shared mapping and specific mapping
mapping = {**shared_mapping, **table_3_specific_mapping}
abbrs_to_names, names_to_definitions = split_mapping(mapping)

# Format p-values and rename columns
df['p-value'] = df['p-value'].apply(format_p_value)
df = df.rename(columns=abbrs_to_names)

# Save as a latex table
to_latex_with_note(df, 'table_3.tex', caption='Comparative Performance of the Random Forest and Elastic Net Models', 
                   label='table:Model_Comparison', note='RF denotes Random Forest model, EN denotes Elastic Net model.', 
                   legend=names_to_definitions)  

