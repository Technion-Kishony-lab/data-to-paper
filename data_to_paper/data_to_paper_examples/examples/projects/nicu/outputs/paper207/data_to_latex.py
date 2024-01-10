
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

shared_mapping: Mapping = {
    'PrePost': ('Treatment Policy', '0: Pre-policy, 1: Post-policy'),
    'AGE': ('Maternal Age', 'Age of Mother at time of childbirth, in years'),
    'GestationalAge': ('Gestational Age', 'Age of pregnancy at the time baby is born, in weeks'),
    'ModeDelivery_VAGINAL': ('Vaginal Delivery', '1: Yes, 0: No'),
    'APGAR1': ('Apgar score at 1 min', 'Scale from 1 to 10'),
    'APGAR5': ('Apgar score at 5 min', 'Scale from 1 to 10'),
    'LengthStay': ('NICU Length of Stay', 'Duration in days'),
    'EndotrachealSuction': ('Endotracheal Suction', 'Whether endotracheal suctioning was performed, 1: Yes, 0: No'),
    'PPV': ('Positive Pressure Ventilation', 'Whether PPV was applied, 1: Yes, 0: No'),
}

# TABLE 1:
df = pd.read_pickle('table_1.pkl')
mapping = {k: v for k, v in shared_mapping.items() if k in df.columns or k in df.index}
abbrs_to_names, legend = split_mapping(mapping)
df.rename(index=abbrs_to_names, inplace=True)
df['p-value'] = df['p-value'].apply(format_p_value)

to_latex_with_note(
    df, 'table_1.tex',
    caption="Test of association between treatment policy change and neonatal treatments", 
    label='table:neonatal_treatments',
    legend=legend
)

# TABLE 2:
df = pd.read_pickle('table_2.pkl')
mapping = {k: v for k, v in shared_mapping.items() if k in df.columns or k in df.index}
mapping |= {
    'U_statistic': ('U-Statistic', None)
}
abbrs_to_names, legend = split_mapping(mapping)
df.rename(index=abbrs_to_names, columns = abbrs_to_names, inplace=True)
df['p-value'] = df['p-value'].apply(format_p_value)

to_latex_with_note(
    df, 'table_2.tex',
    caption="Test of association between the change in treatment policy and neonatal outcomes", 
    label='table:neonatal_outcomes',
    legend=legend
)

# TABLE 3:
df = pd.read_pickle('table_3.pkl')
mapping = {k: v for k, v in shared_mapping.items() if k in df.columns or k in df.index}
mapping |= {
    'PrePolicy': ('Pre-Policy Period','Before the change of policy in 2015'),
    'PostPolicy': ('Post-Policy Period','After the change of policy in 2015')
}
abbrs_to_names, legend = split_mapping(mapping)
df.rename(index=abbrs_to_names, columns = abbrs_to_names, inplace=True)

to_latex_with_note(
    df, 'table_3.tex',
    caption="Comparison of the distribution of confounding variables between the pre-guideline and post-guideline groups", 
    label='table:confounding_variables',
    legend=legend
)
