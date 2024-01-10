

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
    'AGE': ('Mom\'s age', 'Mother\'s age at the time of delivery, years'),
    'BirthWeight': ('Birth Wt.', 'Infant birth weight, Kg'),
    'AntibioticsDuration': ('Antibiotics Dur.', 'Duration of antibiotic treatment, days'),
    'LengthStay': ('Stay Length', 'Duration of stay in the NICU, days'),
    'APGAR1': ('APGAR (1 min)', 'Newborn\'s condition at 1 minute after birth'),
    'APGAR5': ('APGAR (5 min)', 'Newborn\'s condition at 5 minutes after birth')
}

# TABLE 0
df0 = pd.read_pickle('table_0.pkl')
mapping0 = shared_mapping.copy()
mapping0['PrePolicy'] = ('Before Policy Change', '')
mapping0['PostPolicy'] = ('After Policy Change', '')
abbrs_to_names, legend = split_mapping(mapping0)
df0.rename(columns=abbrs_to_names, index=abbrs_to_names, inplace=True)
df0 = df0.transpose()
to_latex_with_note(df0, 
                   'table_0.tex', 
                   caption="Descriptive statistics of key variables stratified by PrePost", 
                   label='table:prepost_stats',
                   legend=legend)

# TABLE 1
df1 = pd.read_pickle('table_1.pkl')
mapping1: Mapping = {
    'Treatment': ('Treatment', 'Type of NICU Treatment Performed'),
    'Chi2_p_value': ('P-value', 'P-value from Chi-square Test for Difference in Treatments Before and After Treatment Change'),
    '1': ('EndoTracheal Suction', ''),
    '2': ('PPV', ''),
    '3': ('Oxygen Therapy', ''),
    '4': ('Mechanical Ventilation', ''),
    '5': ('Surfactant Application', '')
} 
abbrs_to_names, legend = split_mapping(mapping1)
df1.rename(columns=abbrs_to_names, index=abbrs_to_names, inplace=True)
df1['P-value'] = df1['P-value'].apply(format_p_value)
to_latex_with_note(df1, 
                   'table_1.tex',
                   caption="Chi-square test results for the difference in NICU treatments before and after policy change",
                   label='table:treatment_change',
                   legend=legend)

# TABLE 2
df2 = pd.read_pickle('table_2.pkl')
mapping2: Mapping = {
    'Outcome': ('Outcome', 'Type of Neonatal Outcome Measure'),
    't_stat': ('t-statistic', 't-statistic from Independent Sample T-Test'),
    'p_value': ('P-value', 'P-value from Independent Sample T-Test'),
    '1': ('APGAR 1-min Score', ''),
    '2': ('APGAR 5-min Score', ''),
    '3': ('Length of NICU Stay', ''),
    '4': ('Breastfeeding', ''),
    '5': ('SNAPPE II Score', '')
}
abbrs_to_names, legend = split_mapping(mapping2)
df2.rename(columns=abbrs_to_names, index=abbrs_to_names, inplace=True)
df2['P-value'] = df2['P-value'].apply(format_p_value)
to_latex_with_note(df2,
                   'table_2.tex', 
                   caption="T-test results for the difference in neonatal outcomes before and after policy change", 
                   label='table:outcome_change',
                   legend=legend)
