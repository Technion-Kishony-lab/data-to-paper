
# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
    'group_V': ('Vaccinated', 'Only vaccinated group'),
    'group_I': ('Infected', 'Only infected group'),
    'group_H': ('Hybrid', 'Infected and vaccinated group'),
    'mean': ('Mean', 'Average value'),
    'std': ('Standard Deviation', 'Measure of the amount of variation or dispersion of a set of values'),
    'count': ('Count', 'Total number of observations'),
    'ci': ('Confidence Interval', '95% confidence interval around the mean'),
    't-statistic': ('T-Statistic', 'Measure of the size of the difference relative to the variation in your sample data'),
    'p-value': ('P-Value', 'The probability that the results from your sample data occurred by chance'),
    'Coef.': ('Coefficient', 'Measure of the relationship between the dependent and an independent variable'),
    'Std.Err.': ('Standard Error', 'Measure of the statistical accuracy of an estimate'),
    'P>|t|': ('P-Value', 'The hypothesis test which measures the statistical significance of the regression coefficient'),
    'symptom_number': ('Symptom Number', 'Number of symptoms after infection')
}

# TABLE 0:
df0 = pd.read_pickle('table_0.pkl')
mapping0 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df0, k))
abbrs_to_names0, legend0 = split_mapping(mapping0)
df0 = df0.rename(columns=abbrs_to_names0, index=abbrs_to_names0)

# SAVE AS LATEX: Table 0
to_latex_with_note(
    df0, 'table_0.tex',
    caption = "Descriptive Statistics of the dataset",
    label = 'table:descriptive_statistics',
    note = None,
    legend = legend0)

# TABLE 1:
df1 = pd.read_pickle('table_1.pkl')
mapping1 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df1, k))
abbrs_to_names1, legend1 = split_mapping(mapping1)
df1 = df1.rename(columns=abbrs_to_names1, index=abbrs_to_names1)

# SAVE AS LATEX: Table 1
to_latex_with_note(
    df1, 'table_1.tex',
    caption = "Test of association between vaccination status and symptom numbers",
    label = 'table:association_test',
    note = "Test comparing Vaccinated, Infected and Hybrid groups",
    legend = legend1)

# TABLE 2:
df2 = pd.read_pickle('table_2.pkl')
mapping2 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df2, k))
abbrs_to_names2, legend2 = split_mapping(mapping2)
df2 = df2.rename(columns=abbrs_to_names2, index=abbrs_to_names2)

# SAVE AS LATEX: Table 2
to_latex_with_note(
    df2, 'table_2.tex',
    caption = "ANCOVA of symptom number on age and comorbidity",
    label = 'table:ancova',
    note = "Conducting ANCOVA to determine the effect of age and comorbidity on symptom number",
    legend = legend2)
