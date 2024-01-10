
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
 'PhysActivity': ('Physical Activity', 'Physical Activity in past 30 days, 1: Yes, 0: No'),
 'BMI': ('BMI', 'Body Mass Index, kg/m2'),
 'Age': ('Age', '13-level age category in 5 years intervals'),
 'Sex': ('Sex', '0: Female, 1: Male'),
 'Education': ('Education Level', '1: Never attended school, 2: Elementary, 3: Some high school, 4: High school, 5: Some college, 6: College'),
 'Income': ('Income level', 'Income level on a scale of 1-8 (1: <=10K, 2: <=15K, 3: <=20K, 4: <=25K, 5: <=35K, 6: <=50K, 7: <=75K, 8: >75K)'),
}

# TABLE 0:
df = pd.read_pickle('table_0.pkl')
mapping = {k: v for k, v in shared_mapping.items() if k in df.columns or k in df.index}
abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(
 df, 'table_0.tex',
 caption="Mean values of physical activity, BMI, age, and potential confounders stratified by diabetes status", 
 label='table:descriptive_stats',
 legend=legend)


# TABLE 1:
df = pd.read_pickle('table_1.pkl')
df['pvalue'] = df['pvalue'].apply(format_p_value)

mapping = {k: v for k, v in shared_mapping.items() if k in df.index}
mapping |= {
 'pvalue': ('P-value', None),
 'coef': ('Coefficient', None),
 'PhysActivity_BMI': ('Physical Activity * BMI', 'Interaction term between Physical Activity and BMI'),
 'PhysActivity_Age':('Physical Activity * Age', 'Interaction term between Physical Activity and Age'),
 'const': ('Constant', None),
 'std err': ('Standard Error', None)
}

abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(index=abbrs_to_names)

# Save as latex:
to_latex_with_note(
 df, 'table_1.tex',
 caption="Logistic regression of diabetes status on physical activity, BMI, age, and their interaction terms, adjusting for sex, education, and income", 
 label='table:logistic_regression',
 note="pvalue: If value is less than 1e-6, it is represented as less than 1e-6",
 legend=legend)
