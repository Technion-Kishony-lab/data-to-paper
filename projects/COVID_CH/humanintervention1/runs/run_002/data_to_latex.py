
# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
    'N': ('No Imm.', 'No immunity'),
    'I': ('Inf. Only', 'Infected, unvaccinated'),
    'V': ('Vac. Only', 'Twice vaccinated, uninfected'),
    'H': ('Hyb.', 'Hybrid: Infected & Vaccinated'),
    'delta': (None, 'Delta Variant'),
    'omicron': (None, 'Omicron Variant'),
    'coef': ('Coeff.', None),
    'p-value': ('P-val', None),
}

# TABLE 0:
df0 = pd.read_pickle('table_0.pkl')

# RENAME ROWS AND COLUMNS 
mapping0 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df0, k)) 
mapping0 |= {
    'Average Symptom Number': ('Avg. Symp.', 'Average Number of Symptoms'),
    'Standard Deviation': ('Std. Dev.', 'Standard Deviation of Symptoms'),
    'Count': ('Count', 'Total number of infected individuals in each group and variant'),
}
abbrs_to_names0, legend0 = split_mapping(mapping0)
df0 = df0.rename(columns=abbrs_to_names0, index=abbrs_to_names0)

# SAVE AS LATEX:
to_latex_with_note(
    df0, 'table_0.tex',
    caption="Avg. symptom no. by immunity group & variant", 
    label='table:dist_symp',
    note="Includes only positive cases.",
    legend=legend0)

# TABLE 1:
df1 = pd.read_pickle('table_1.pkl')

# RENAME ROWS AND COLUMNS 
mapping1 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df1, k)) 
mapping1 |= {
    'Intercept': ('Intercept', None),
    'age': ('Age', None),
    'sex[T.male]': ('Sex (M)', 'Male Sex'),
    'comorbidity': ('Comorb.', '1: Yes, 0: No'),
    'group[T.I]': ('Inf. Only', 'Infected, unvaccinated'),
    'group[T.N]': ('No Imm.', 'No immunity'),
    'group[T.V]': ('Vac. Only', 'Twice vaccinated, uninfected'),
}
abbrs_to_names1, legend1 = split_mapping(mapping1)
df1 = df1.rename(index=abbrs_to_names1)

# SAVE AS LATEX:
to_latex_with_note(
    df1, 'table_1.tex',
    caption="Association between symptom numbers and immunity group", 
    label='table:symp_grp',
    note="Adjusted for age, sex, and comorbidities",
    legend=legend1)

# TABLE 2:
df2 = pd.read_pickle('table_2.pkl')

# RENAME ROWS AND COLUMNS 
mapping2 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df2, k)) 
mapping2 |= {
    'Intercept': ('Intercept', None),
    'age': ('Age', None),
    'sex[T.male]': ('Sex (M)', 'Male Sex'),
    'comorbidity': ('Comorb.', '1: Yes, 0: No'),
    'variant[T.omicron]': ('Var. (O)', 'Omicron Variant'),
    'group[T.I]:variant[T.omicron]': ('Inf. Only * O', 'Interaction term for Infected Only and Omicron Variant'),
    'group[T.N]:variant[T.omicron]': ('No Imm. * O', 'Interaction term for No Immunity and Omicron Variant'),
    'group[T.V]:variant[T.omicron]': ('Vac. Only * O', 'Interaction term for Vaccinated Only and Omicron Variant'),
    'group[T.I]': ('Inf. Only', 'Infected, unvaccinated'),
    'group[T.N]': ('No Imm.', 'No immunity'),
    'group[T.V]': ('Vac. Only', 'Twice vaccinated, uninfected'),
}
abbrs_to_names2, legend2 = split_mapping(mapping2)
df2 = df2.rename(index=abbrs_to_names2)

# SAVE AS LATEX:
to_latex_with_note(
    df2, 'table_2.tex',
    caption="Symptom numbers, immunity group, variant, interaction", 
    label='table:symp_inter',
    note="Adjusted for age, sex, and comorbidities",
    legend=legend2)
