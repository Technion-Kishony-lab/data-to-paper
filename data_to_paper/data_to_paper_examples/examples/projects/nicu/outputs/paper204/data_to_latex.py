
# IMPORT
import pandas as pd
from typing import Dict, Tuple, Optional
from my_utils import to_latex_with_note, format_p_value

Mapping = Dict[str, Tuple[Optional[str], Optional[str]]]

def split_mapping(d: Mapping):
 abbrs_to_names = {abbr: name for abbr, (name, definition) in d.items() if name is not None}
 names_to_definitions = {name or abbr: definition for abbr, (name, definition) in d.items() if definition is not None}
 return abbrs_to_names, names_to_definitions

# PREPARATION FOR ALL TABLES
shared_mapping: Mapping = {
 'HypertensiveDisorders': ('Hypertensive Disorders', 'Prevalence of gestational hypertensive disorder, 1: Yes, 0: No'),
 'MaternalDiabetes': ('Maternal Diabetes', 'Prevalence of gestational diabetes, 1: Yes, 0: No'),
 'GestationalAge': ('Gestational Age', 'Gestational age at the time of delivery, in weeks'),
 'BirthWeight': ('Birth Weight', 'Weight of the newborn, in kilograms'),
 'APGAR1': ('APGAR Score at 1 min', 'APGAR score of the newborn at 1 minute post birth'),
 'APGAR5': ('APGAR Score at 5 min', 'APGAR score of the newborn at 5 minutes post birth'),
 'LengthStay': ('Length of Stay', 'Duration of newborn stay at Neonatal ICU, in days'),
 'PPV': ('PPV', 'Positive Pressure Ventilation, 1: Yes, 0: No'),
 'EndotrachealSuction': ('Endotracheal Suction', 'Whether endotracheal suctioning was performed, 1: Yes, 0: No'),
 'CardiopulmonaryResuscitation': ('Cardiopulmonary Resuscitation', 'Cardiopulmonary Resuscitation performed, 1: Yes, 0: No'),
}


# For renaming and adding definitions for columns.
def transform_df(df, custom_mapping: Mapping):
    mapping = {k: v for k, v in shared_mapping.items() if k in df.columns or k in df.index}
    mapping.update(custom_mapping)
    abbrs_to_names, legend = split_mapping(mapping)
    return df.rename(columns=abbrs_to_names, index=abbrs_to_names), legend

# TABLE 0:
df = pd.read_pickle('table_0.pkl')
df, legend = transform_df(df, {})
# Save as latex:
to_latex_with_note(
 df, 'table_0.tex',
 caption="Descriptive statistics of key variables stratified by pre and post policy implementation", 
 label='table:desc_stats',
 legend=legend)

# TABLE 1:
df = pd.read_pickle('table_1.pkl')
custom_mapping: Mapping = {
    'Chi-square': ('Chi-square statistic', 'Value of Chi-square statistic for the categorical treatment data'),
    'p-value': ('p-value', 'Corresponding p-value for the Chi-square test'),
}
df, legend = transform_df(df, custom_mapping)
df['p-value'] = df['p-value'].apply(format_p_value)
# Save as latex:
to_latex_with_note(
 df, 'table_1.tex',
 caption="Comparison of treatment options pre and post policy implementation", 
 label='table:treatment_comparison',
 legend=legend)

# TABLE 2:
df = pd.read_pickle('table_2.pkl')
custom_mapping: Mapping = {
    'T-statistic': ('T-statistic', 'Value of T-statistic for the treatment outcome data'),
    'p-value': ('p-value', 'Corresponding p-value for the T-test'),
}
df, legend = transform_df(df, custom_mapping)
df['p-value'] = df['p-value'].apply(format_p_value)
# Save as latex:
to_latex_with_note(
 df, 'table_2.tex',
 caption="Comparison of outcomes pre and post policy implementation measured by duration of stay and Apgar scores", 
 label='table:outcome_comparison',
 legend=legend)

