
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
 'AGE': ('Avg. Age', 'Average age of the mother, years'),
 'GestationalAge': ('Avg. Gestational Age', 'Average gestational age, weeks'),
 'BirthWeight': ('Avg. Birth Wt.', 'Average birth weight in kilograms'),
 'APGAR1': ('Avg. APGAR1 Score', 'Average 1 minute APGAR score (scale from 1 to 10)'),
 'APGAR5': ('Avg. APGAR5 Score', 'Average 5 minute APGAR score (scale from 1 to 10)'),
 'LengthStay': ('Avg. NICU stay', 'Average length of stay at Neonatal Intensive Care Unit, in days'),
 'SNAPPE_II_SCORE': ('Avg. SNAPPE-II Score', 'Average Score for Neonatal Acute Physiology with Perinatal Extension-II, score range: 0–20 (mild), 21–40 (moderate), 41 and higher (severe)'),
}

# TABLE 0
df0 = pd.read_pickle('table_0.pkl')

# Transpose data
df0 = df0.T

# Apply shared mapping
mapping = {k: v for k, v in shared_mapping.items() if k in df0.columns or k in df0.index}
abbrs_to_names, legend = split_mapping(mapping)
df0 = df0.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex
to_latex_with_note(
 df0, 'table_0.tex',
 caption='Summary of key variables before and after new policy', 
 label='table:SummaryVariables',
 legend=legend)


# TABLE 1
df1 = pd.read_pickle('table_1.pkl')

# Renaming the labels with scientifically-suitable names
mapping1: Mapping = {
 'Chi-square': ('Chi-square', 'Chi-square Test Statistic'),
 'p-value': ('P-value', 'Computed P-value'),
 'Treatment': ('Treatment', 'Types of Neonatal Treatments'),
 'PPV': ('PPV (Positive Pressure Ventilation)', 'Whether positive pressure ventilation was performed, 1:Yes, 0:No'),
 'EndotrachealSuction': ('Endotracheal Suction', 'Whether endotracheal suctioning was performed, 1:Yes, 0:No'),
 'MeconiumRecovered': ('Meconium Recovered', 'Whether Meconium was recovered, 1:Yes, 0:No'),
 'CardiopulmonaryResuscitation': ('Cardiopulmonary Resuscitation', 'Whether cardiopulmonary resuscitation was performed, 1:Yes, 0:No'),
 'RespiratoryReasonAdmission': ('Reason for Admission - Respiratory ', 'Admission due to respiratory reason, 1:Yes, 0:No'),
 'RespiratoryDistressSyndrome': ('Respiratory Distress Syndrome', 'Presence of respiratory distress syndrome, 1:Yes, 0:No'),
 'TransientTachypnea': ('Transient Tachypnea', 'Presence of transient tachypnea, 1:Yes, 0:No'),
 'MeconiumAspirationSyndrome': ('Meconium Aspiration Syndrome', 'Presence of meconium aspiration syndrome, 1:Yes, 0:No'),
 'OxygenTherapy': ('Oxygen Therapy', 'Whether oxygen therapy was given, 1:Yes, 0:No'),
 'MechanicalVentilation': ('Mechanical Ventilation', 'Mechanical Ventilation performed, 1:Yes, 0:No')
}

abbrs_to_names1, legend1 = split_mapping(mapping1)
df1 = df1.rename(columns=abbrs_to_names1, index=abbrs_to_names1)

# Formatting P-value
df1["P-value"] = df1["P-value"].map(format_p_value)

# Save as latex
to_latex_with_note(
 df1, 'table_1.tex',
 caption='Association between change in new treatment policy and changes in treatments', 
 label='table:TreatmentPolicyChange',
 legend=legend1
)

# TABLE 2
df2 = pd.read_pickle('table_2.pkl')

# Renaming abbreviated labels
mapping2: Mapping = {
 'Coeff': ('Coefficient', 'Coefficients from the Linear Regression Model'),
 'p-value': ('P-value', 'Computed P-value'),
 'Outcome': ('Outcome', 'Neonatal Outcomes'),
 'APGAR1': ('APGAR1 Score', '1 minute APGAR score (scale from 1 to 10)'),
 'APGAR5': ('APGAR5 Score', '5 minute APGAR score (scale from 1 to 10)'),
 'LengthStay': ('Length of NICU Stay', 'Length of stay at the Neonatal Intensive Care Unit, in days'),
 'SNAPPE_II_SCORE': ('SNAPPE-II Score', 'Score for Neonatal Acute Physiology with Perinatal Extension-II,score range: 0–20 (mild), 21–40 (moderate), 41 and higher (severe)'),
}

abbrs_to_names2, legend2 = split_mapping(mapping2)
df2 = df2.rename(columns=abbrs_to_names2, index=abbrs_to_names2)

# Formatting P-value
df2["P-value"] = df2["P-value"].map(format_p_value)

# Save as latex
to_latex_with_note(
 df2, 'table_2.tex',
 caption='Linear regression analysis of impact of policy change on neonatal outcomes', 
 label='table:PolicyImpactOutcomes',
 legend=legend2)

