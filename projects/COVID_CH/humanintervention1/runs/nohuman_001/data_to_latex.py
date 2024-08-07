
# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
# Shared mapping for labels that are common to both tables
shared_mapping: AbbrToNameDef = {
    'group_N[T.True]': ('Not Immun', None),
    'group_V[T.True]': ('Vacc', None),
    'group_I[T.True]': ('Inf', None),
    'sex_female[T.True]': ('Fem', '1: Yes, 0: No'),
    'BMI_u30[T.True]': ('BMI < 30', '1: <30, 0: >=30'),
    'patient_contact': ('P. Contact', '1: Yes, 0: No'),
    'using_FFP2_mask': ('Use FFP2', '1: Yes, 0: No'),
}

# TABLE 1:
df1 = pd.read_pickle('table_1.pkl')

# RENAME ROWS AND COLUMNS 
mapping1 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df1, k)) 
mapping1.update({'Coef.': ('Coef', None), 
                 'Std.Err.': ('SE', None),
                 'z': ('Z-Score', None),
                 'P>|z|': ('P-value', None),
                 'age': ('Age', 'years')})

abbrs_to_names1, legend1 = split_mapping(mapping1)
df1 = df1.rename(columns=abbrs_to_names1, index=abbrs_to_names1)

# SAVE AS LATEX
to_latex_with_note(
    df1, 'table_1.tex',
    caption="Association between various factors and time until reinfection", 
    label='table:time_until_reinfection',
    note="Statistical analyses performed using Generalized Linear Models (GLM).",
    legend=legend1)

# TABLE 2:
df2 = pd.read_pickle('table_2.pkl')

# RENAME ROWS AND COLUMNS  
mapping2 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df2, k)) 
mapping2.update({'Coef.': ('Coef', None), 
                 'Std.Err.': ('SE', None),
                 'z': ('Z-Score', None),
                 'P>|z|': ('P-value', None),
                 'age': ('Age', 'years')})

abbrs_to_names2, legend2 = split_mapping(mapping2)
df2 = df2.rename(columns=abbrs_to_names2, index=abbrs_to_names2)

# SAVE AS LATEX
to_latex_with_note(
    df2, 'table_2.tex',
    caption="Association between vaccination status and number of symptoms at reinfection", 
    label='table:symptoms_at_reinfection',
    note="Statistical analyses performed using Generalized Linear Models (GLM).",
    legend=legend2, 
    columns=['Coef', 'SE', 'P-value'])
