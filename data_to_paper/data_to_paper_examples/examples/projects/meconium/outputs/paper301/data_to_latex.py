
# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, is_str_in_df, split_mapping, AbbrToNameDef 

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
    'AGE': ('Maternal Age', 'Maternal age, years'),
    'GRAVIDA': ('Gravida', 'Total number of pregnancies for a woman'),
    'CI': (None, '95% Confidence Interval')
}

# TABLE 0:
df0 = pd.read_pickle('table_0.pkl')

# RENAME ROWS AND COLUMNS
mapping0 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df0, k)) 
mapping0 |= {
    'GestationalAge': ('Gestational Age', 'Age of the fetus in weeks')
}
abbrs_to_names0, legend0 = split_mapping(mapping0)
df0 = df0.rename(columns=abbrs_to_names0, index=abbrs_to_names0)

# SAVE AS LATEX:
to_latex_with_note(
    df0, 'table_0.tex',
    caption="Summary of Maternal Age, Gravida, and Gestational Age.", 
    label='table:Summary_Stats',
    note="Average maternal age, gravidity, and gestational age of infants.",
    legend=legend0)


# TABLE 1:
df1 = pd.read_pickle('table_1.pkl')

# RENAME ROWS AND COLUMNS
mapping1 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df1, k)) 
mapping1 |= {
    'PPV': ('Positive Pressure Ventilation', '1: Yes, 0: No'),
    'EndotrachealSuction': ('Endotracheal Suction', '1: Yes, 0: No'),
    'Chi2 Statistic': ('Chi-Squared Statistic', None),
    'p-value': ('P-value', None)
}
abbrs_to_names1, legend1 = split_mapping(mapping1)
df1 = df1.rename(columns=abbrs_to_names1, index=abbrs_to_names1)

# SAVE AS LATEX:
to_latex_with_note(
    df1, 'table_1.tex', 
    caption="Impact of change in treatment policy on neonatal treatments.",
    label='table:Neonate_Treatments', 
    note="Chi-squared test results on neonatal treatments.", 
    legend=legend1)


# TABLE 2:
df2 = pd.read_pickle('table_2.pkl')

# RENAME ROWS AND COLUMNS
mapping2 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df2, k)) 
mapping2 |= {
    'Length Of Stay': ('Length Of Stay', 'Duration of stay in the NICU, days'),
    'APGAR1 Score': ('APGAR1 Score', 'APGAR score at 1 minute after birth, 1-10'),
    'APGAR5 Score': ('APGAR5 Score', 'APGAR score at 5 minutes after birth, 1-10'),
    'T-Statistic': ('T-statistic', 'Test statistic from t-test'), 
    'p-value': ('P-value', None)
}
abbrs_to_names2, legend2 = split_mapping(mapping2)
df2 = df2.rename(columns=abbrs_to_names2, index=abbrs_to_names2)

# SAVE AS LATEX:
to_latex_with_note(
    df2, 'table_2.tex',
    caption="Impact of change in treatment policy on neonatal outcomes.",
    label='table:Neonate_Outcomes',
    note="T-test results on neonatal outcomes.",
    legend=legend2)

