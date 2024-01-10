

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
 'PhysActivity': ('Phys. Act.', 'Physical Activity in past 30 days (0=no, 1=yes)'),
 'HighBP': ('High BP', 'High Blood Pressure (0=no, 1=yes)'),
 'HighChol': ('High Chol.', 'High Cholesterol (0=no, 1=yes)'),
 'HeartDiseaseorAttack': ('Heart Dis./Att.', 'Coronary heart disease (CHD) or myocardial infarction (MI), (0=no, 1=yes)'),
 'P>|z|':('P-value', 'P-value of the logistic regression model'),
 'z': ('z-score', 'Z-score for the coefficient in the logistic regression model'),
 'Coef.': ('Coeff.', 'Estimated model coefficient'),
 'Std.Err.': ('Std Err.', 'Standard error for the estimated coefficient'),
 '[0.025': ('CI Lower', '95% Confidence Interval Lower Bound'),
 '0.975]': ('CI Upper', '95% Confidence Interval Upper Bound')
}

# TABLE 0:
df = pd.read_pickle('table_0.pkl')

# RENAME ROWS AND COLUMNS
mapping = {k: v for k, v in shared_mapping.items() if k in df.columns or k in df.index}
abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(df, 'table_0.tex',
                   caption="Descriptive Statistics of Physical Activity and Chronic Health Conditions for both Diabetes and Non-Diabetes Individuals", 
                   label='table:diabetes_comparison',
                   note="Values represent the proportions of individuals",
                   legend=legend)

# TABLE 1:
df = pd.read_pickle('table_1.pkl')

# FORMAT VALUES 
df['P>|z|'] = df['P>|z|'].apply(format_p_value)

# RENAME COLUMN AND ROW NAMES
mapping = {k: v for k, v in shared_mapping.items() if k in df.columns or k in df.index}
abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as Latex
to_latex_with_note(df, 'table_1.tex',
                   caption="Association between Physical Activity and High BP in Individuals with Diabetes", 
                   label='table:physical_activity_high_blood_pressure',
                   note="Values represent logistic regression coefficients. P-values are two-sided.",
                   legend=legend)


# TABLE 2:
df = pd.read_pickle('table_2.pkl')

# FORMAT VALUES 
df['P>|z|'] = df['P>|z|'].apply(format_p_value)

# RENAME COLUMN AND ROW NAMES
mapping = {k: v for k, v in shared_mapping.items() if k in df.columns or k in df.index}
abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as Latex
to_latex_with_note(df, 'table_2.tex',
                   caption="Association between Physical Activity and High Chol. in Individuals with Diabetes",
                   label='table:physical_activity_high_cholesterol',
                   note="Values represent logistic regression coefficients. P-values are two-sided.",
                   legend=legend)


# TABLE 3:
df = pd.read_pickle('table_3.pkl')

# FORMAT VALUES 
df['P>|z|'] = df['P>|z|'].apply(format_p_value)

# RENAME COLUMN AND ROW NAMES
mapping = {k: v for k, v in shared_mapping.items() if k in df.columns or k in df.index}
abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)


# Save as Latex
to_latex_with_note(df, 'table_3.tex',
                   caption="Association between Physical Activity and Heart Dis./Att. in Individuals with Diabetes",
                   label='table:physical_activity_heart_disease',
                   note="Values represent logistic regression coefficients. P-values are two-sided.",
                   legend=legend)
