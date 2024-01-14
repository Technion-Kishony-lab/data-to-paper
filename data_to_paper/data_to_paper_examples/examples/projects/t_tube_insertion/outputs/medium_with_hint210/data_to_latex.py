
# IMPORT
import pandas as pd
from typing import Dict, Any, Optional, Tuple
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES

shared_mapping: AbbrToNameDef = {
    'wt': ('Weight', 'Patient weight, kg'),
    'ht': ('Height', 'Patient height, cm'),
    'sex': ('Sex', 'Patient sex, {0: "female", 1: "male"}'),
    'tube_depth_G': ('OTTD', 'Optimal tracheal tube depth as determined by chest X-ray, cm'),
    'age_c': ('Age', 'Patient age, rounded to half years'),
}

# REUSABLE FUNCTION
def convert_to_tex(df, filename: str, caption: str, label: str, mapping, note: str = None):
    abbrs_to_names, legend = split_mapping(mapping)
    df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)
    to_latex_with_note(df, filename, caption, f'table:{label}', note, legend)

# TABLE 0:
df = pd.read_pickle('table_0.pkl')

# RENAME ROWS AND COLUMNS
mapping_table_0 = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)} 
convert_to_tex(df, 
               filename='table_0.tex', 
               caption='Descriptive statistics of the dataset, stratified by sex', 
               label='descriptive', 
               mapping=mapping_table_0)

# TABLE 3:
df = pd.read_pickle('table_3.pkl')

# FORMAT VALUES
df['p_value'] = df['p_value'].apply(format_p_value)

# RENAME ROWS AND COLUMNS
mapping_table_3 = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)} 
mapping_table_3 |= {
    't_statistic': ('T-Statistic', None),
    'p_value': ('P-value', 'P-value from T-statistic test')
}

convert_to_tex(df, 
               filename='table_3.tex', 
               caption='Comparison between the Height Formula and Random Forest Model', 
               label='comparison', 
               mapping=mapping_table_3)
