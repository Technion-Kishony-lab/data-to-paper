
# IMPORT
import pandas as pd
from typing import Dict, Tuple, Optional
from my_utils import to_latex_with_note, format_p_value

Mapping = Dict[str, Tuple[Optional[str], Optional[str]]]

def split_mapping(d: Mapping):
    abbrs_to_names = {abbr: name for abbr, (name, definition) in d.items() if name is not None}
    names_to_definitions = {name or abbr: definition for abbr, (name, definition) in d.items() if definition is not None}
    return abbrs_to_names, names_to_definitions

# PREPARATION FOR ALL TABLES
shared_mapping: Mapping = {
    'PhysActivity': ('P. Act.', 'Physical Activity in past 30 days (0=no, 1=yes)'),
    'BMI': ('BMI', 'Body Mass Index'),
    'Age': ('Age Cat.', '13-level age category in intervals of 5 years (1=18-24, 2=25-29, ..., 12=75-79, 13=80 or older)'),
    'Sex': ('Sex', 'Sex (0=female, 1=male)'),
    'Diabetes_Status': ('Diab. Status', 'Diabetes (0=no, 1=yes)'),
}

# TABLE 0:
df = pd.read_pickle('table_0.pkl')

# Renaming Abbreviated Columns and Rows
mapping = {k: v for k, v in shared_mapping.items() if k in df.columns or k in df.index}
mapping |= {
  'mean': ('Mean', None),
  'std': ('Std Dev', None),
}
abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(
 df, 
 'table_0.tex',
 caption="Mean and Std Dev of P. Act., BMI, Age Cat., and Sex stratified by Diab. Status", 
 label='table:table_0',
 note="Mean values are likely to be altered due to approximations",
 legend=legend)

# TABLE 1:
df = pd.read_pickle('table_1.pkl')

# Formatting P-Values
df['P>|t|'] = df['P>|t|'].apply(format_p_value)

# Renaming Abbreviated Columns and Rows
mapping = {k: v for k, v in shared_mapping.items() if k in df.columns or k in df.index}
mapping |= {
  'const': ('Intercept', None),
  'Coef.': ('Coeff.', 'Coefficient Estimate'),
  'Std.Err.': ('Std Err', None),
  't': ('t-stat', None),
  'P>|t|': ('P-val', None),
  '[0.025': ('CI Lower', None),
  '0.975]': ('CI Upper', None),
}
abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(
 df,
 'table_1.tex',
 caption="Multiple Linear Regression Model predicting glycemic control among individuals with diabetes, adjusting for age, sex, and BMI.", 
 label='table:table_1',
 note="P-val denotes P-value for given coefficients. CI Lower & CI Upper are boundaries of 95% Confidence Interval.", 
 legend=legend)
