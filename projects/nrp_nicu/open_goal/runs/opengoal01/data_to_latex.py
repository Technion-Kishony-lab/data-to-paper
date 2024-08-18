
# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
    'AGE': ('Maternal Age', 'Maternal Age, years'),
    'GestationalAge': ('Gestational Age', 'Gestational Age, weeks'),
    'BirthWeight': ('Birth Weight', 'Birth Weight, KG'),
}

# TABLE 0:
df0 = pd.read_pickle('table_0.pkl')

# RENAME ROWS AND COLUMNS
mapping0 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df0, k))
mapping0 |= {
    'AGE (mean)': ('Mean Maternal Age', None),
    'AGE (std)': ('Standard Deviation Maternal Age', None),
    'GestationalAge (mean)': ('Mean Gestational Age', None),
    'GestationalAge (std)': ('Standard Deviation Gestational Age', None),
    'BirthWeight (mean)': ('Mean Birth Weight', None),
    'BirthWeight (std)': ('Standard Deviation Birth Weight', None),
    'PrePost': ('Policy Implementation', '0: Pre 2015 policy, 1: Post 2015 policy'),
}

abbrs_to_names0, legend0 = split_mapping(mapping0)
df0 = df0.rename(columns=abbrs_to_names0, index=abbrs_to_names0)

# SAVE AS LATEX:
to_latex_with_note(
    df0, 'table_0.tex',
    caption="Descriptive statistics of important numerical variables across the Pre and Post policy implementation groups", 
    label='table:descriptives',
    note="Values are represented as mean and standard deviation. The values in the table are grouped by the implementation of the policy (Pre or Post 2015 policy).",
    legend=legend0)

# TABLE 1:
df1 = pd.read_pickle('table_1.pkl')

# RENAME ROWS AND COLUMNS
mapping1 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df1, k)) 
mapping1 |= {
    'chi-square': ('Chi-Square', 'Chi-Square Statistic for the Test'),
    'p-value': ('P-value', 'P-value for the Test'),
    'df': ('Degrees of Freedom', 'Degrees of Freedom for the Test'),
    'EndotrachealSuction': ('Endotracheal Suction', 'Was endotracheal suctioning performed on the infants? (1: Yes, 0: No)'),
    'MechanicalVentilation': ('Mechanical Ventilation', 'Was mechanical ventilation performed on the infants? (1: Yes, 0: No)')
}

abbrs_to_names1, legend1 = split_mapping(mapping1)
df1 = df1.rename(index=abbrs_to_names1, columns=abbrs_to_names1)

# SAVE AS LATEX:
to_latex_with_note(df1, 
                   'table_1.tex', 
                   caption="Test of association between policy change and rates of Endotracheal Suction and Mechanical Ventilation, considering confounding factors", 
                   label='table:tests',
                   legend=legend1)

# TABLE 2:
df2 = pd.read_pickle('table_2.pkl')

# RENAME ROWS AND COLUMNS
mapping2 = {
    'MeconiumAspirationSyndrome': ('Meconium Aspiration Syndrome', 'Measured in Meconium Aspiration Syndrome'),
    'RespiratoryDistressSyndrome': ('Respiratory Distress Syndrome', 'Measured in Respiratory Distress Syndrome'),
    'Pneumothorax': ('Pneumothorax', 'Measured in Pneumothorax'),
    'Significant': ('Significance', 'Significance at 5% level (Yes: p-value < 0.05, No: p-value >= 0.05)'),
    'OR': ('Odds Ratio', 'Odds Ratio from the Logistic Regression'),
}

abbrs_to_names2, legend2 = split_mapping(mapping2)
df2 = df2.rename(index=abbrs_to_names2, columns=abbrs_to_names2)

# Transpose dataframe
df2 = df2.transpose()

# SAVE AS LATEX:
to_latex_with_note(df2, 
                   'table_2.tex', 
                   caption="Logistic regression impact of the NRP guideline change on occurrence of Meconium Aspiration Syndrome, Respiratory Distress Syndrome, and Pneumothorax; considers confounders", 
                   label='table:logistic',
                   legend=legend2)
