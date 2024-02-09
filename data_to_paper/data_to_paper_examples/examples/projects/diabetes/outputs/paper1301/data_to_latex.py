
# IMPORT
import pandas as pd
from typing import Dict, Tuple, Optional
from my_utils import to_latex_with_note, format_p_value

Mapping = Dict[str, Tuple[Optional[str], Optional[str]]]


# PREPARATION FOR ALL TABLES
def split_mapping(d: Mapping):
    abbrs_to_names = {abbr: name for abbr, (name, definition) in d.items() if name is not None}
    names_to_definitions = {name or abbr: definition for abbr, (name, definition) in d.items() if definition is not None}
    return abbrs_to_names, names_to_definitions

shared_mapping: Mapping = {
    'PhysActivity': ('Physical Act.', '0: No activity, 1: Any activity'),
    'BMI': ('BMI', "Body Mass Index"),
    'Age': ('Age', 'Age in intervals of 5 years. 1: 18-24 --> 13: 80+ yrs'),
    'Smoker': ('Smoker', '0: Non-smoker, 1: Smoker'),
    'HighBP': ('High BP', '0: No high BP, 1: High BP'),
    'HighChol': ('High Chol', '0: No high chol, 1: High chol'),
    'Education': ('Ed.', 'Education level. 1: None --> 6: College'),
    'Income': ('Income', 'Income category. 1: <=10K --> 8: >75K'),
    'Coef.': ('Coef.', None),
    'Std.Err.': ('Std.Err.', None),
    'z': ('Z', 'Standardized test statistic'),
    'P>|z|': ('P-value', 'Significance level of the Z statistic')
}

# TABLE 0:
df0 = pd.read_pickle('table_0.pkl')

mapping0 = {'mean': ('Mean', None), 'std': ('Std.Dev', None)}
abbrs_to_names, legend = split_mapping(mapping0)
df0.rename(columns=abbrs_to_names, index=abbrs_to_names, inplace=True)

to_latex_with_note(
    df0, 
    'table_0.tex', 
    caption="Descriptive statistics of Physical Activity stratified by Diabetes", 
    label='table:descriptive_statistics_0',
    legend=legend)

# TABLE 1:
df1 = pd.read_pickle('table_1.pkl')
abbrs_to_names, legend = split_mapping(shared_mapping)
df1.rename(columns=abbrs_to_names, index=abbrs_to_names, inplace=True)

# FORMAT VALUES
df1['P-value'] = df1['P-value'].apply(format_p_value)

to_latex_with_note(
    df1, 
    'table_1.tex',
    caption="Association between  physical activity and diabetes prevalence",
    label='table:activity_and_diabetes_1',
    legend=legend)

# TABLE 2:
df2 = pd.read_pickle('table_2.pkl')

mapping2 = dict(shared_mapping.items())
mapping2.update({
    'PhysActivity:BMI': ('Activity*BMI', "Interaction term between physical activity and BMI"),
})

abbrs_to_names, legend = split_mapping(mapping2)
df2.rename(columns=abbrs_to_names, index=abbrs_to_names, inplace=True)

# FORMAT VALUES
df2['P-value'] = df2['P-value'].apply(format_p_value)

to_latex_with_note(
    df2, 
    'table_2.tex',
    caption="Moderating effect of BMI on the association between physical activity and diabetes",
    label='table:activity_and_diabetes_2',
    legend=legend)
