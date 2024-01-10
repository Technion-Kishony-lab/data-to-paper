
# IMPORT
import pandas as pd
from typing import Dict, Tuple, Optional
from my_utils import to_latex_with_note, format_p_value

Mapping = Dict[str, Tuple[Optional[str], Optional[str]]]

# PREPARATION FOR ALL TABLES
def split_mapping(d: Mapping):
    abbrs_to_names = {abbr: (name or abbr) for abbr, (name, definition) in d.items() if name is not None}
    names_to_definitions = {name or abbr: definition for abbr, (name, definition) in d.items() if definition is not None}
    return abbrs_to_names, names_to_definitions

shared_mapping: Mapping = {
    'PPV': ('PPV', 'Positive Pressure Ventilation? 1: Yes, 0: No'),
    'EndotrachealSuction': ('ETS', 'Endotracheal Suction? 1: Performed, 0: Not Performed'),
    'APGAR1': ('A1', '1-min APGAR score'),
    'APGAR5': ('A5', '5-min APGAR score'),
    'LengthStay': ('Stay', 'Length of stay, days'),
}

# TABLE 0
df0 = pd.read_pickle('table_0.pkl').T
mapping0 = {k: v for k, v in shared_mapping.items() if k in df0.columns or k in df0.index}
column_names0, legend0 = split_mapping(mapping0)
df0.rename(columns=column_names0, index=column_names0 , inplace=True)

to_latex_with_note(
 df0, 'table_0.tex',
 caption="Descriptive statistics of neonate interventions and outcomes stratified by new policy", 
 label='table:descriptive-statistics',
 legend=legend0)

# TABLE 1
df1 = pd.read_pickle('table_1.pkl')
mapping1 = {k: v for k, v in shared_mapping.items() if k == df1.index[0] or k == df1.index[1]}
index_names1, legend1 = split_mapping(mapping1)
df1.rename(index=index_names1, inplace=True)
df1['p-value'] = df1['p-value'].apply(format_p_value)

to_latex_with_note(
 df1, 'table_1.tex',
 caption="Test of association between new policy implementation and interventions", 
 label='table:association-interventions',
 legend=legend1)

# TABLE 2
df2 = pd.read_pickle('table_2.pkl')
mapping2 = {k: v for k, v in shared_mapping.items() if k in df2.index}
index_names2, legend2 = split_mapping(mapping2)
df2.rename(index=index_names2, inplace=True)
df2['p-value'] = df2['p-value'].apply(format_p_value)

to_latex_with_note(
 df2, 'table_2.tex',
 caption="Test of association between new policy and neonatal outcomes", 
 label='table:association-outcomes',
 legend=legend2)
