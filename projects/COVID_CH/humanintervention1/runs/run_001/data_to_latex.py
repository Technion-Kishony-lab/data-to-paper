
# IMPORT 
import pandas as pd 
from my_utils import to_latex_with_note, is_str_in_df, split_mapping, AbbrToNameDef 

# PREPARATION FOR ALL TABLES 
shared_mapping: AbbrToNameDef = { 
    'coef': ('Coefficient', 'Estimated effect on the symptom number'), 
    'p-value': ('P-value', 'Statistical significance of the estimated effect'),
    'sex[T.male]': ('Male Sex', 'If the sex is male, 1: Yes, 0: No'),
    'age': ('Age', 'Age in years'), 
    'comorbidity': ('Comorbidity', 'If any pre-existing comorbity existed, 1: Yes, 0: No'),  
} 

# TABLE 0: 
df0 = pd.read_pickle('table_0.pkl') 

# Prepare the data mappings for table 0 

mapping0: AbbrToNameDef = { 
    'Average Symptom Number': ('Mean Symptoms', 'Average number of symptoms from delta or omicron variant infection'), 
    'Standard Deviation': ('Std. Dev.', 'Standard deviation of symptom counts for delta or omicron variant infection'), 
    'Count': ('Infections', 'Number of delta or omicron variant infections'),
    'H': ('Hybrid', 'Infected and at least one vaccination'),
    'I': ('Infected Only', 'Infected and not vaccinated'),
    'N': ('Not Immune', 'Neither infected nor vaccinated'), 
    'V': ('Vaccinated Only', 'Vaccinated but not infected'), 
} 
abbrs_to_names0, legend0 = split_mapping({**mapping0}) 
df0 = df0.rename(columns=abbrs_to_names0, index=abbrs_to_names0) 

# Save as LaTeX: 
to_latex_with_note( 
    df0, 'table_0.tex', 
    caption='Summary statistics of health worker infections by different SARS-CoV-2 variants', 
    label='table:summary_statistics', 
    note='Summary statistics including the count of health worker infections, average symptom count, and \
    standard deviation of symptom counts for different virus variants.', 
    legend=legend0) 

# TABLE 1: 

df1 = pd.read_pickle('table_1.pkl') 

# Prepare the data mappings for table 1 
mapping1: AbbrToNameDef = {
    'group[T.I]': ('Group Infected Only', 'Infected but not vaccinated'),
    'group[T.N]': ('Group Not Immune', 'Neither infected nor vaccinated'), 
    'group[T.V]': ('Group Vaccinated Only', 'Vaccinated but not infected'), 
    'variant[T.omicron]': ('Omicron Variant', 'If the variant of SARS-CoV-2 virus is omicron, 1: Yes, 0: No'), 
} 
abbrs_to_names1, legend1 = split_mapping({**shared_mapping, **mapping1}) 
df1 = df1.rename(columns=abbrs_to_names1, index=abbrs_to_names1) 

# Save as LaTeX: 
to_latex_with_note( 
    df1, 'table_1.tex', 
    caption='Model estimates of the factors influencing symptom numbers', 
    label='table:model_estimates', 
    note='Table reports the pooled OLS regression coefficient estimates which give associations between symptom numbers and immunity group, variant of virus, and adjustment for impacted factors.', 
    legend=legend1) 

# TABLE 2: 
df2 = pd.read_pickle('table_2.pkl') 

# Prepare the data mappings for table 2 
mapping2: AbbrToNameDef = { 
    'group[T.I]:variant[T.omicron]': ('Group Infected Only:Omicron Variant', 'Interaction between being in the Infected Only group and the omicron variant'),
    'group[T.N]:variant[T.omicron]': ('Group Not Immune:Omicron Variant', 'Interaction between being in the Not Immune group and the omicron variant'),
    'group[T.V]:variant[T.omicron]': ('Group Vaccinated Only:Omicron Variant', 'Interaction between being in the Vaccinated Only group and the omicron variant'),
} 
abbrs_to_names2, legend2 = split_mapping({**shared_mapping, **mapping1, **mapping2}) 
df2 = df2.rename(columns=abbrs_to_names2, index=abbrs_to_names2) 

# Save as LaTeX: 
to_latex_with_note( 
    df2, 'table_2.tex', 
    caption='Model estimates for interaction effects', 
    label='table:interaction_effects', 
    note='Table reports the pooled OLS regression coefficient estimates which give interaction effects between symptom numbers and immunity group, variant of virus, adjustment for impacted factors.', 
    legend=legend2) 
