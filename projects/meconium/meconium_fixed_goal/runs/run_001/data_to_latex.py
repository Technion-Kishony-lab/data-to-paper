
# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
    'std': ('Standard deviation (SD)', None),
    'mean': ('Mean', None),
    'Chi2': ('Chi-sq stat', None), 
    'p_value': ('p-value', None),
    'T_statistic': ('T statistic', None),
    'APGAR1': (None, '1 minute APGAR score: a standard measure of a newborn infant’s acclimatization to extrauterine life'),
    'APGAR5': (None, '5 minutes APGAR score: a standard measure of a newborn infant’s progress in adapting to extrauterine life'),
    'SNAPPE_II_SCORE': ('SNAPPE II score', 'The Score for Neonatal Acute Physiology with Perinatal Extension II'),
    'PPV': ('PPV', 'Positive Pressure Ventilation performed?\n1: Yes, 0: No'),
    'EndotrachealSuction': ('Endotracheal suction', 'Endotracheal suctioning performed?\n1: Yes, 0: No'),
    'MeconiumRecovered': ('Meconium recovered', 'Was Meconium recovered?\n1: Yes, 0: No')
}

# TABLE 0
df0 = pd.read_pickle('table_0.pkl')

df0 = df0.T # Transpose the dataframe

# RENAME ROWS AND COLUMNS
mapping0 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df0, k)) 
mapping0 |= {
    'APGAR1_mean': ('Mean of 1 min APGAR', None),
    'APGAR1_std': ('SD of 1 min APGAR', None),
    'APGAR5_mean': ('Mean of 5 min APGAR', None),
    'APGAR5_std': ('SD of 5 min APGAR', None),
    'SNAPPE_II_SCORE_mean': ('Mean of SNAPPE II', None),
    'SNAPPE_II_SCORE_std': ('SD of SNAPPE II', None),
}

abbrs_to_names0, legend0 = split_mapping(mapping0)
df0 = df0.rename(index=abbrs_to_names0)

legend0.update({
    '0': 'Before guidelines change',
    '1': 'After guidelines change'
})

# SAVE AS LATEX
to_latex_with_note(
    df0, 'table_0.tex', 
    caption="Mean and Standard deviation of APGAR scores and SNAPPE II score, stratified by guidelines change", 
    label='table:change_in_policy_impact', 
    legend=legend0)

# TABLE 1
df1 = pd.read_pickle('table_1.pkl')

# RENAME ROWS AND COLUMNS
mapping1 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df1, k)) 

abbrs_to_names1, legend1 = split_mapping(mapping1)
df1 = df1.rename(columns=abbrs_to_names1, index=abbrs_to_names1)

# SAVE AS LATEX
to_latex_with_note(
    df1, 'table_1.tex', 
    caption="Association between treatments and change in policy using Chi-square test", 
    label='table:association_tests', 
    legend=legend1)

# TABLE 2
df2 = pd.read_pickle('table_2.pkl')

# RENAME ROWS AND COLUMNS
mapping2 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df2, k))

abbrs_to_names2, legend2 = split_mapping(mapping2)
df2 = df2.rename(columns=abbrs_to_names2)

# SAVE AS LATEX
to_latex_with_note(
    df2, 'table_2.tex', 
    caption="Difference in APGAR scores between pre and post intervention groups using independent t-test", 
    label='table:difference_tests', 
    legend=legend2)

