
# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, is_str_in_df, split_mapping, AbbrToNameDef
from typing import Any, Dict, Optional, Tuple

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
    "mean": ("Mean", "Mean value"),
}

# TABLE 0:
df0 = pd.read_pickle('table_0.pkl')

# RENAME ROWS AND COLUMNS 
mapping0: AbbrToNameDef = {
    'female': ('Female', None),
    'male': ('Male', None),
    'H': ('Hybrid Immunity', None),
    'V': ('Vaccinated', None), 
}

# Merge with shared_mapping
mapping0.update(shared_mapping)

abbrs_to_names0, legend0 = split_mapping(mapping0)
df0.rename(columns=abbrs_to_names0, index=abbrs_to_names0, inplace=True)

to_latex_with_note(
    df0, 'table_0.tex',
    caption="Descriptive statistics of Age stratified by Sex and Immunity Group", 
    label='table:table0',
    note="Values shown are standardized",
    legend=legend0
)


# TABLE 2:
df2 = pd.read_pickle('table_2.pkl')

# RENAME ROWS AND COLUMNS 
mapping2: AbbrToNameDef = {
    'mean': ('Mean', 'Mean standardized symptom count'),
    't-statistic': ('t-statistic', 't-value from independent samples t-test'),
    'p-value': ('p-value', 'p-value from independent samples t-test'),
    '95% CI': ('95% Confidence Interval', "95% Confidence Interval for the Mean standardized symptom count"),
    'Booster Shot=no': ('No Booster Shot', None),
    'Booster Shot=yes': ('Booster Shot Received', None),
}

# Merge with shared_mapping
mapping2.update(shared_mapping)

abbrs_to_names2, legend2 = split_mapping(mapping2)
df2.rename(columns=abbrs_to_names2, index=abbrs_to_names2, inplace=True)

to_latex_with_note(
    df2, 'table_2.tex',
    caption="Association between booster shot & symptom count", 
    label='table:table2',
    note="Mean and 95% Confidence Interval estimated using independent samples t-test",
    legend=legend2
)
