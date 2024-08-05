
# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
    'Coef.': ('Coefficient', None),
    'Std.Err.': ('Std. Error', None),
    'z': ('z-value', None),
    'P>|z|':('p-value', None),
    't': ('t-value', None),
    'P>|t|':('p-value', None),
    'BMI': ('BMI Category','"o30" for over 30  or "u30" for below 30'),
}

# TABLE 1
df1 = pd.read_pickle('table_1.pkl')

## RENAME ROWS AND COLUMNS
mapping1 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df1, k)) 
mapping1 |= {
    'group_V[T.True]': ('Vaccinated Group', 'Twice vaccinated, uninfected'),
    'group_I[T.True]': ('Infected Group', 'Infected, unvaccinated'),
    'group_H[T.True]': ('Hybrid Group', 'Infected and ≥1 vaccination, referred to as Hybrid immunity'),
    'total_time_at_risk': ('Total Time at Risk', 'Total time at risk for infection in the given group')
}
abbrs_to_names1, legend1 = split_mapping(mapping1)
df1 = df1.rename(columns=abbrs_to_names1, index=abbrs_to_names1)

# SAVE AS LATEX
to_latex_with_note(
    df1, 'table_1.tex',
    caption="Impact of vaccination group on infection event and total time at risk", 
    label='table:table1EffectOfVaccinationGroup',
    legend=legend1)

# TABLE 2
df2 = pd.read_pickle('table_2.pkl')

## RENAME ROWS AND COLUMNS
mapping2 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df2, k)) 
mapping2 |= {
    'group_V[T.True]': ('Vaccinated Group', 'Twice vaccinated, uninfected'),
    'group_I[T.True]': ('Infected Group', 'Infected, unvaccinated'),
    'group_H[T.True]': ('Hybrid Group', 'Infected and ≥1 vaccination, referred to as Hybrid immunity')
}
abbrs_to_names2, legend2 = split_mapping(mapping2)
df2 = df2.rename(columns=abbrs_to_names2, index=abbrs_to_names2)

# SAVE AS LATEX
to_latex_with_note(
    df2, 'table_2.tex',
    caption="Vaccination group impact on total time at risk among infected individuals", 
    label='table:table2VaccinatedGroupTimeAtRisk',
    legend=legend2)

# TABLE 3
df3 = pd.read_pickle('table_3.pkl')

## RENAME ROWS AND COLUMNS
mapping3 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df3, k)) 
mapping3 |= {
    'H': ('Hybrid Immunity Group', 'Infected and ≥1 vaccination, referred to as Hybrid immunity'),
    'I': ('Infected Group', 'Infected, unvaccinated'),
    'N': ('No Immunity Group', 'No immunity'),
    'V': ('Vaccinated Group', 'Twice vaccinated, uninfected'),
    'infection_rate': ('Infection Rate', 'Rate of infection within the respective group')
}
abbrs_to_names3, legend3 = split_mapping(mapping3)
df3 = df3.rename(columns=abbrs_to_names3, index=abbrs_to_names3)

# SAVE AS LATEX
to_latex_with_note(
    df3, 'table_3.tex',
    caption="Distribution of infection events by vaccination group", 
    label='table:table3InfectionDistribution',
    legend=legend3)
