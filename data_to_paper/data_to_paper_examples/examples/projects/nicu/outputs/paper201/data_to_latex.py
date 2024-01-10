
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
    'AGE': ('Maternal Age', 'Age of the mother, years'),
    'GRAVIDA': ('Gravidity', 'Number of times the mother was pregnant'),
    'PARA': ('Parity', 'Number of times the mother has given birth to a fetus with gestational age >20 weeks'),
    'GestationalAge': ('Gestational Age', 'Gestational age, weeks'),
    'BirthWeight': ('Birth Weight', 'Birth weight of the neonate, KG'),
    'OxygenTherapy': ('Oxygen Therapy', 'Whether oxygen therapy was given to the neonate, 0: No, 1: Yes'),
    'LengthStay': ('Length of Stay', 'Length of stay at NICU, days'),
}


# TABLE 0:
df = pd.read_pickle('table_0.pkl')

mapping = {k: v for k, v in shared_mapping.items() if k in df.columns or k in df.index}

abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(
    df, 'table_0.tex',
    caption="Descriptive Statistics of Selected Variables",
    label='table:desc_stats',
    legend=legend)


# TABLE 1:
df = pd.read_pickle('table_1.pkl')

mapping = {
    'Treatment': ('Intervention', 'The particular treatment given to the neonate'),
    'Chi2 Value': ('Chi-square stat.', 'Chi-square statistic from the test'),
    'p-value': ('P-value', 'P-value of the test')
}

abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)
df['P-value'] = df['P-value'].apply(format_p_value)

# Save as latex:
to_latex_with_note(
    df, 'table_1.tex',
    caption="Comparison of Interventions Pre and Post Guideline Changes",
    label='table:compare_interventions',
    legend=legend)


# TABLE 2:
df = pd.read_pickle('table_2.pkl')

mapping = {
    'Outcome Measures': ('Outcome Measures', 'The particular outcome measure of interest'),
    'p-value': ('P-value', 'P-value of the test controlling for confounding variables'),
    'F Value': ('F Value', 'Value of the F statistic from the test controlling for confounding variables')
}

abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)
df['P-value'] = df['P-value'].apply(format_p_value)

# Save as latex:
to_latex_with_note(
    df, 'table_2.tex',
    caption="Comparison of Neonatal Outcomes Pre and Post Guideline Changes",
    label='table:compare_outcomes',
    legend=legend)
