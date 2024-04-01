
# IMPORT
import pandas as pd
from typing import Optional, Dict, Any, Tuple
from my_utils import to_latex_with_note, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = { 
    'State_codes_from': ('Src State', None),
    'State_codes_to': ('Dst State', None),
    'nodeFrom': ('Src ID', 'ID of the sender node'),
    'same_chamber': ('Same Chamber', 'Interactions within same legislative chamber. Yes:1, No:0'),
    'Coef.': ('Coeff', None),
    'Std.Err.': ('Std Err', 'Standard Error'),
    '[0.025': ('CI Low', 'Confidence Interval Lower Limit'),
    '0.975]': ('CI High', 'Confidence Interval Upper Limit'),
    'z': ('Z Score', 'Z-statistic for the estimated coefficients'),
}

# TABLE 1
df1 = pd.read_pickle('table_1.pkl')

# TRANSPOSE THE TABLE
df1 = df1.T

# RENAME ROWS AND COLUMNS 
mapping1 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df1, k)) 
mapping1 |= {
    'P>|z|': (None, 'P-value of Z-statistic'),
}

abbrs_to_names1, legend1 = split_mapping(mapping1)
df1 = df1.rename(columns=abbrs_to_names1, index=abbrs_to_names1)

# SAVE AS LATEX
to_latex_with_note(
    df1, 'table_1.tex',
    caption="Test of association between state representation and interaction on Twitter.", 
    label='table:StateTwitterInteraction',
    note="This table presents the coefficients from the logistic regression.",
    legend=legend1)


# TABLE 2
df2 = pd.read_pickle('table_2.pkl')

# RENAME ROWS AND COLUMNS 
mapping2 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df2, k)) 

abbrs_to_names2, legend2 = split_mapping(mapping2)
df2 = df2.rename(columns=abbrs_to_names2, index=abbrs_to_names2)

# SAVE AS LATEX
to_latex_with_note(
    df2, 'table_2.tex',
    caption="Test of association between legislative chamber and frequency of Twitter interactions.", 
    label='table:ChamberTwitterInteraction',
    note="This table presents the coefficients from the Poisson regression.",
    legend=legend2)
