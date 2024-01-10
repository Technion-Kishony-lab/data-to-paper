
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
    'PPV': ('PPV', '1: Positive Pressure Ventilation applied, 0: Not Applied'),
    'EndotrachealSuction': ('ES', '1: Endotracheal Suctioning performed, 0: Not Performed'),
    'AntibioticsDuration': ('AD', 'Duration of neonate antibiotic treatment, days'),
    'LengthStay': ('LOS', 'Length of stay at NICU, days'),
    'APGAR1': ('Apgar Score at 1m', 'Apgar score of the baby at 1 minute after birth'),
    'OxygenTherapy': ('OT', '1: Oxygen Therapy applied, 0: Not applied'),
    'PrePost': ('Policy Change', '0: Pre 2015, 1: Post 2015'),
    'SNAPPE_II_SCORE': ('SNAPPE-II Score', 'Score of the neonatal acute physiology assessment, higher values indicate worse condition'),
    'GestationalAge': ('GA', 'Gestational age at birth, weeks'),
    'RespiratoryDistressSyndrome': ('RDS', '1: Neonate has Respiratory Distress Syndrome, 0: No RDS'),
    'APGAR5': ('Apgar Score at 5m', 'Apgar score of the baby at 5 minutes after birth'),
    'AGE': ('Maternal Age', 'Age of the mother at delivery, years'),
    'ProlongedRupture': ('PR', '1: Prolonged rupture of membranes, 0: No PR'),
    'MeconiumAspirationSyndrome': ('MAS', '1: Neonate has Meconium Aspiration Syndrome, 0: No MAS')
}

# TABLE 0:
df = pd.read_pickle('table_0.pkl')
df = df.transpose() 

mapping = {k: v for k, v in shared_mapping.items() if k in df.columns or k in df.index}
abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

to_latex_with_note(
 df, 'table_0.tex',
 caption="Descriptive statistics before and after the 2015 policy change", 
 label='table:desc_stats',
 legend=legend)

# TABLE 1:
df = pd.read_pickle('table_1.pkl')

mapping = {k: v for k, v in shared_mapping.items() if k in df.columns or k in df.index}
mapping |= {
 'coef': ('Coefficient', None),
 'p-value': ('P-value', None),
}
abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

df['P-value'] = df['P-value'].apply(format_p_value)

to_latex_with_note(
 df, 'table_1.tex',
 caption="Association between policy change and PPV", 
 label='table:policy_ppv',
 legend=legend)

# TABLE 2:
df = pd.read_pickle('table_2.pkl')

mapping = {k: v for k, v in shared_mapping.items() if k in df.columns or k in df.index}
mapping |= {
 'coef': ('Coefficient', None),
 'p-value': ('P-value', None),
}
abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

df['P-value'] = df['P-value'].apply(format_p_value)

to_latex_with_note(
 df, 'table_2.tex',
 caption="Association between policy change and Length of Stay", 
 label='table:policy_los',
 legend=legend)

# TABLE 3:
df = pd.read_pickle('table_3.pkl')

mapping = {k: v for k, v in shared_mapping.items() if k in df.columns or k in df.index}
mapping |= {
 'coef': ('Coefficient', None),
 'p-value': ('P-value', None),
}
abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

df['P-value'] = df['P-value'].apply(format_p_value)

to_latex_with_note(
 df, 'table_3.tex',
 caption="Association between policy change and Antibiotics Duration",
 label='table:policy_ad',
 legend=legend)
