
# IMPORT
import pandas as pd
from typing import Dict, Tuple, Optional
from my_utils import to_latex_with_note, format_p_value

Mapping = Dict[str, Tuple[Optional[str], Optional[str]]]

# PREPARATION FOR ALL TABLES
def split_mapping(d: Mapping):
    abbrs_to_names = {abbr: name for abbr, (name, definition) in d.items() if name is not None}
    names_to_definitions = {name or abbr: definition for abbr, (name, definition) in d.items() if definition is not None}
    return abbrs_to_names, names_to_definitions

# shared mapping for all tables
shared_mapping: Mapping = {
    '0': ('Pre-2015', 'Neonatal outcomes and treatments before 2015'),
    '1': ('Post-2015', 'Neonatal outcomes and treatments after 2015'),
    'mean': ('Mean', None),
    'std': ('Std dev.', 'Standard Deviation'),
    'APGAR1': ('Apgar Score at 1 min', None),
    'EndotrachealSuction': ('Endotracheal Suction', '1: Yes, 0: No'),
    'PPV': ('Positive Pressure Ventilation', '1: Yes, 0: No'),
    'LengthStay': ('Length of Stay (days)', None),
    'p_value': ('P-value', None)
}

# TABLE 0
df = pd.read_pickle('table_0.pkl')

mapping = {k: v for k, v in shared_mapping.items() if k in df.columns or k in df.index}
abbrs_to_names, legend = split_mapping(mapping)

df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)
to_latex_with_note(
 df, 'table_0.tex',
 caption="Means and standard deviations of treatments and outcomes before and after 2015", 
 label='table:descriptive_stats_0',
 legend=legend
)

# TABLE 1
df = pd.read_pickle('table_1.pkl')

mapping = {k: v for k, v in shared_mapping.items() if k in df.columns or k in df.index}
abbrs_to_names, legend = split_mapping(mapping)

df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)
df = df.applymap(format_p_value)

to_latex_with_note(
 df, 'table_1.tex',
 caption="Association between treatment policy and treatments", 
 label='table:association_treatments_1',
 note=None,
 legend=legend
)

# TABLE 2
df = pd.read_pickle('table_2.pkl')

mapping = {k: v for k, v in shared_mapping.items() if k in df.columns or k in df.index}
abbrs_to_names, legend = split_mapping(mapping)

df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)
df = df.applymap(format_p_value)

to_latex_with_note(
 df, 'table_2.tex',
 caption="Comparison of neonatal outcomes before and after guideline implementation", 
 label='table:neonatal_outcomes_2',
 note=None,
 legend=legend
)

