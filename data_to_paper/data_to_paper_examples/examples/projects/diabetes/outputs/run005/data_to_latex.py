
# IMPORT
import pandas as pd
from typing import Dict, Any, Optional, Tuple
from my_utils import to_latex_with_note, is_str_in_df, split_mapping, AbbrToNameDef

# Type Aliases
AbbrToNameDef = Dict[Any, Tuple[Optional[str], Optional[str]]]

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
    'Fruits': ('Fruit', None),
    'Veggies': ('Veggies', None),
    'Income': ('Income', 'Income level on a scale of 1 to 8 (1= <=10K, 2= <=15K, 3= <=20K, 4= <=25K, 5= <=35K, 6= <=50K, 7= <=75K, 8= >75K)'),
    'Fruits:Income': ('F-Income', 'Interaction between Fruit consumption and Income'),
    'Veggies:Income': ('V-Income', 'Interaction between Vegetable consumption and Income'),
    'z': ('z', 'z-value or z-score is the coefficient divided by its standard error.'),
}

# TABLE 1:
df1 = pd.read_pickle('table_1.pkl')

# extracting relevant labels from shared_mapping
mapping1 = {k: v for k, v in shared_mapping.items() if is_str_in_df(df1, k)}
abbrs_to_names1, legend1 = split_mapping(mapping1)
df1.rename(columns=abbrs_to_names1, index=abbrs_to_names1, inplace=True)

# Rename longer column names
df1.rename(columns={'Std.Err.': 'Std.Err', 'P>|z|': 'P>|z|',
                    '[0.025': '[0.025', '0.975]': '0.975'
                    }, inplace=True)

to_latex_with_note(
    df1,
    'table_1.tex',
    caption="Association between diet and the risk of diabetes, adjusted for different confounders.",
    label='table:table_1',
    legend=legend1)

# TABLE 2:
df2 = pd.read_pickle('table_2.pkl')

mapping2 = {k: v for k, v in shared_mapping.items() if is_str_in_df(df2, k)}
abbrs_to_names2, legend2 = split_mapping(mapping2)
df2.rename(columns=abbrs_to_names2, index=abbrs_to_names2, inplace=True)

# Rename longer column names
df2.rename(columns={'Std.Err.': 'Std.Err', 'P>|z|': 'P>|z|',
                    '[0.025': '[0.025', '0.975]': '0.975'
                    }, inplace=True)

to_latex_with_note(
    df2,
    'table_2.tex',
    caption="Moderating effect of income on the relationship between diet and the risk of diabetes.",
    label='table:table_2',
    legend=legend2)
