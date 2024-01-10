

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
 'Pre-policy': ('Before Policy Change', None),
 'Post-policy': ('After Policy Change', None),
 '0': ('No Endotracheal Suction', 'Endotracheal suction was not performed'),
 '1': ('Performed Endotracheal Suction', 'Endotracheal suction was performed'),
 'Chi-squared': ('Chi-squared', None),
 'p-value': ('P-value', None),
}

# TABLE 1:
df = pd.read_pickle('table_1.pkl')

# FORMAT VALUES
# Format the p-value
df['p-value'] = df['p-value'].apply(format_p_value)

# RENAME ROWS AND COLUMNS
mapping = {k: v for k, v in shared_mapping.items() if k in df.columns or k in df.index}
abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(
 df, 'table_1.tex',
 caption="Perform Chi-Square Test for Neonatal Endotracheal Suction before and after new policy", 
 label='table:endotracheal_suction_chi2',
 legend=legend)

# TABLE 2:

# Reset the shared_mapping for table 2
shared_mapping: Mapping = {
 't-statistic': ('T-Statistic', 'T-statistics from independent two-sample t-test'),
 'p-value': ('P-value', 'P-value from independent two-sample t-test'),
 'APGAR5 score comparison': ('APGAR Score Comparison', 'Comparison of 5 min APGAR Score before and after policy change'),
}

df = pd.read_pickle('table_2.pkl')

# FORMAT VALUES
df['p-value'] = df['p-value'].apply(format_p_value)

# RENAME ROWS AND COLUMNS
mapping = {k: v for k, v in shared_mapping.items() if k in df.columns or k in df.index}
abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(
 df, 'table_2.tex',
 caption="Perform T-test for APGAR5 Scores before and after the policy change", 
 label='table:APGAR5_ttest',
 legend=legend)

