
# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, format_p_value
from typing import Dict, Tuple, Optional

Mapping = Dict[str, Tuple[Optional[str], Optional[str]]]

# PREPARATION FOR ALL TABLES
def split_mapping(d: Mapping):
    abbrs_to_names = {abbr: name for abbr, (name, definition) in d.items() if name is not None}
    names_to_definitions = {name or abbr: definition for abbr, (name, definition) in d.items() if definition is not None}
    return abbrs_to_names, names_to_definitions

shared_mapping: Mapping = {
     'Fruits': ('Fruits Consumption', 'Consumes one fruit or more each day (0=no, 1=yes)'),
     'Veggies': ('Vegetables Consumption', 'Consumes one Vegetable or more each day (0=no, 1=yes)'),
     'HighChol': ('High Cholesterol', 'High Cholesterol level (0=no, 1=yes)'),
     'Diabetes': ('Diabetes', 'Diabetes condition (0=no, 1=yes)'),
     'BMI': ('Body Mass Index', None),
     'Age': ('Age Category', '13-level age category in intervals of 5 years')
     }

# TABLE 0:
df = pd.read_pickle('table_0.pkl')

mapping = {k: v for k, v in shared_mapping.items() if k in df.columns or k in df.index}
mapping.update({"Row"+str(i): ('Row'+str(i), 'Statistic Row '+str(i)) for i in range(1, 5)})

abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

to_latex_with_note(
 df, 'table_0.tex',
 caption="Diabetes prevalence in relation to fruit and vegetable consumption.", 
 label='table:diabetes_fruit_veggie',
 legend=legend)

# TABLE 1:
df = pd.read_pickle('table_1.pkl')

df['p-value'] = df['p-value'].apply(format_p_value)

mapping = {k: v for k, v in shared_mapping.items() if k in df.index}
mapping['const'] = ('Intercept', None)

abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(index=abbrs_to_names)

to_latex_with_note(
 df, 'table_1.tex',
 caption="Multiple Logistic Regression Model: predicting diabetes with fruit and vegetable consumption, while controlling for Body Mass Index and Age.",
 label='table:multi_logit_model',
 note="*** p<0.001, ** p<0.01, * p<0.05, . p<0.1",
 legend=legend)
