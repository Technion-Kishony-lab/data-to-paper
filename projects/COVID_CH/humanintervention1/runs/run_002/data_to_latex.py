
# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
    'coef': (None, 'Regression coefficient'),
    'p-value': (None, 'p-value of the hypothesis test'),
    'group[T.I]': ('Infected', 'Group: Infected and not vaccinated'),
    'group[T.N]': ('None', 'Group: No immunity before study'),
    'group[T.V]': ('Vaccinated', 'Group: Vaccinated and not infected before study'),
    'sex[T.male]': ('Male', 'Sex of participant'),
    'variant[T.omicron]': ('Omicron', 'Omicron variant of SARS-CoV-2'),
    'I': ('Infected', 'Group: Infected and not vaccinated'),
    'N': ('None', 'Group: No immunity before study'),
    'V': ('Vaccinated', 'Group: Vaccinated and not infected before study')
}

# TABLE 0:
df0 = pd.read_pickle('table_0.pkl')

# DROP UNNECESSARY COLUMNS
df0.drop(columns='Standard Deviation', inplace=True) 

# RENAME ROWS/COLUMNS
mapping0 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df0, k)) 
mapping0 |= {
    'Average Symptom Number': ('Avg. Symptoms', 'Average number of symptoms'),
    'Count': ('Cases', 'Total number of cases'),
    'H': ('Hybrid', 'Group: Infected and vaccinated')
}

abbrs_to_names0, legend0 = split_mapping(mapping0)
df0.rename(columns=abbrs_to_names0, index=abbrs_to_names0, inplace=True)

# SAVE AS LATEX
to_latex_with_note(
    df0, 'table_0.tex',
    caption='Distribution of Average Symptom Count by Group and Variant',
    label='table:AvgSymptomCount',
    legend=legend0)


# TABLE 1
df1 = pd.read_pickle('table_1.pkl')

# RENAME ROWS/COLUMNS
mapping1 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df1, k)) 
mapping1 |= {
    'age': ('Age', 'Age in Years'),
    'comorbidity': ('Comorb.', 'Existence of pre-existing comorbidities'),
    'Intercept': (None, 'The constant term in regression analysis')
}

abbrs_to_names1, legend1 = split_mapping(mapping1)
df1.rename(index=abbrs_to_names1, inplace=True)

# SAVE AS LATEX
to_latex_with_note(
    df1, 'table_1.tex',
    caption='Regression Analysis: Symptom Count and Group, Age, Sex, Comorbidity',
    label='table:Regression1',
    legend=legend1)


# TABLE 2
df2 = pd.read_pickle('table_2.pkl')

# RENAME ROWS/COLUMNS
mapping2 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df2, k)) 
mapping2 |= {
    'group[T.I]:variant[T.omicron]': ('Infected * Omicron', 'Interaction: Infected Unvaccinated and Omicron Variant'),
    'group[T.N]:variant[T.omicron]': ('None * Omicron', 'Interaction: No Immunity and Omicron Variant'),
    'group[T.V]:variant[T.omicron]': ('Vaccinated * Omicron', 'Interaction: Vaccinated Unvaccinated and Omicron Variant'),
    'age': ('Age', 'Age in Years'),
    'comorbidity': ('Comorb.', 'Existence of pre-existing comorbidities'),
    'Intercept': (None, 'The constant term in the regression analysis')
}

abbrs_to_names2, legend2 = split_mapping(mapping2)
df2.rename(index=abbrs_to_names2, inplace=True)

# SAVE AS LATEX
to_latex_with_note(
    df2, 'table_2.tex',
    caption='Regression Analysis: Symptom Count, Group, Variant, Interactions, Age, Sex, Comorbidity',
    label='table:Regression2',
    legend=legend2)
