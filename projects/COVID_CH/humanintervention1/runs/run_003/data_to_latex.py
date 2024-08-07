
# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
    'Coef.': ('Coefficient', 'Coefficient of the regression model'),
    'Std.Err.': ('Std. Err.', 'Standard Error'),
    'P>|t|': ('p-value', 'The probability under a specific statistical model (null hypothesis)'),
    'MeanSymptoms': ('Mean Symptom Count', 'Average number of symptoms reported by each group'),
    'MeanMonthsSinceImmunisation': ('Mean Mos. Since Immun.', 'Average duration (in months) since the last immunisation event'),
    'InfectionEvents': ('Infection Events', 'Number of infection events reported by each group'),
    'H': ('Hybrid Immunity', 'Healthworker infected and ≥1 vaccination'),
    'I': ('Infection Immunity', 'Healthworker infected, unvaccinated'),
    'N': ('No Immunity', 'Healthworker with no immunity'),
    'V': ('Vaccine Immunity', 'Healthworker twice vaccinated, uninfected'),
    't': ('t-stat', 'Computed t-statistic value'),
}

# TABLE 0:
df0 = pd.read_pickle('table_0.pkl')
mapping0 = {
    k: v for k, v in shared_mapping.items() if is_str_in_df(df0, k)
}
abbrs_to_names0, legend0 = split_mapping(mapping0)
df0.rename(columns=abbrs_to_names0, index=abbrs_to_names0, inplace=True)

# SAVE AS LATEX:
to_latex_with_note(
    df0, 'table_0.tex',
    caption="Summary Statistics of Infection Events, Mean Symptoms and Months Since Last Immunisation",
    label='table:summary_stats',
    note="Data aggregated by immunity status.",
    legend=legend0)

# TABLE 1:
df1 = pd.read_pickle('table_1.pkl')
mapping1 = {
    k: v for k, v in shared_mapping.items() if is_str_in_df(df1, k)
}
mapping1 |= {
    'scaled_months_since_immunisation': ('Time Since Immun.', 'Time (in months) since last immunisation'),
    'group_V[T.True]': ('Vaccine Group', 'Healthworker twice vaccinated, uninfected'),
    'group_I[T.True]': ('Infected Group', 'Healthworker infected, unvaccinated'),
    'group_V_interaction': ('Vac. & Time', 'Interaction: Vaccine Group and Time Since Immunization'),
    'group_I_interaction': ('Inf. & Time', 'Interaction: Infected Group and Time Since Immunization'),
}
abbrs_to_names1, legend1 = split_mapping(mapping1)
df1.rename(columns=abbrs_to_names1, index=abbrs_to_names1, inplace=True)
to_latex_with_note(
    df1, 'table_1.tex',
    caption="Association Between Time Since Immunisation and Symptom Number",
    label='table:time_symptoms',
    note="Includes interaction term between immunity group and time since immunisation. Coefficients estimated from an ordinary least squares regression.",
    legend=legend1)

# TABLE 2:
df2 = pd.read_pickle('table_2.pkl')
mapping2 = {
    k: v for k, v in shared_mapping.items() if is_str_in_df(df2, k)
}
mapping2 |= {
    'patient_contact': ('Patient Contact', '1 if healthcare worker has contact with patients'),
    'using_FFP2_mask_x': ('Using FFP2', '1 if healthcare worker uses FFP2 protective respiratory masks'),
    'positive_household_binary': ('Household Contact', '1 if a household contact was positive for SARS-CoV-2 within same month'),
}
abbrs_to_names2, legend2 = split_mapping(mapping2)
df2.rename(columns=abbrs_to_names2, index=abbrs_to_names2, inplace=True)
to_latex_with_note(
    df2, 'table_2.tex',
    caption="Association Between Patient Contact and Number of Symptoms",
    label='table:patient_symptoms',
    note="Model adjusts for mask usage and recent household infections.",
    legend=legend2)
