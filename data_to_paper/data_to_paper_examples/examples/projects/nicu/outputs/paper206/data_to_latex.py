
# IMPORT
import pandas as pd
from typing import Dict, Tuple, Optional
import pickle
from my_utils import to_latex_with_note, format_p_value

Mapping = Dict[str, Tuple[Optional[str], Optional[str]]]

# PREPARATION FOR ALL TABLES
def split_mapping(d: Mapping):
  abbrs_to_names = {abbr: name for abbr, (name, definition) in d.items() if name is not None}
  names_to_definitions = {name or abbr: definition for abbr, (name, definition) in d.items() if definition is not None}
  return abbrs_to_names, names_to_definitions

shared_mapping: Mapping = {
 'AGE': ('M. Age', 'Maternal Age in Years'),
 'BirthWeight': ('Birth Wt.', 'Weight of newborn at birth, KG'),
 'GestationalAge': ('G. Age', 'Pregnancy Age, weeks'),
 'LengthStay': ('Stay Len.', 'Duration of NICU stay, days'),
 'SNAPPE_II_SCORE': ('SNAPPE II', 'Score ranges from 0 (mild) to over 40 (severe)'),
 'ModeDelivery': ('MDeliv', 'Method of Delivery, VAGINAL or CS (C. Section)'),
 'Sepsis': ('Seps', 'Neonatal blood culture ("NO CULTURES", "NEG CULTURES", "POS CULTURES")'),
 'Gender': ('Gen.', '"M"/ "F"'),
 'MeconiumConsistency': ('Mec. Consis.', '"THICK" / "THIN"'),
 'ReasonAdmission': ('R. Admission', 'Neonate ICU admission reason. ("OTHER", "RESP" or "CHORIOAMNIONITIS")'),
}

# TABLE 0:
df_0 = pd.read_pickle('table_0.pkl')

# RENAME ROWS AND COLUMNS
mapping_0 = {k: v for k, v in shared_mapping.items() if k in df_0.columns or k in df_0.index}
abbrs_to_names_0, legend_0 = split_mapping(mapping_0)

# Transpose to make table narrower
df_0 = df_0.T.rename(columns=abbrs_to_names_0, index=abbrs_to_names_0)

# Save as latex:
to_latex_with_note(
 df_0, 'table_0.tex',
 caption="Selected descriptive statistics of the dataset stratified by policy change", 
 label='table:descriptive',
 note="Table 0 presents the summary statistics for the dataset, stratified by the policy change.",
 legend=legend_0)

# TABLE 1:
df_1 = pd.read_pickle('table_1.pkl')

# FORMAT VALUES
df_1['p-value'] = df_1['p-value'].apply(format_p_value)

# Save as latex:
to_latex_with_note(
 df_1, 'table_1.tex',
 caption="Test of treatment changes due to policy changes", 
 label='table:treatment_changes',
 note="Table 1 presents the statistical test of the treatment changes due to policy changes.")

# TABLE 2:
df_2 = pd.read_pickle('table_2.pkl')

# FORMAT VALUES
df_2['p-value'] = df_2['p-value'].apply(format_p_value)

# Save as latex:
to_latex_with_note(
 df_2, 'table_2.tex',
 caption="Test of neonatal outcomes due to policy changes", 
 label='table:neonatal_outcomes',
 note="Table 2 presents the statistical test of the neonatal outcomes due to policy changes.")
