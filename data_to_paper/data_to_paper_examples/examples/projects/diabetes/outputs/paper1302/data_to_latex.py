
# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, is_str_in_df, split_mapping, AbbrToNameDef
from typing import Dict, Tuple, Optional, Any

AbbrToNameDef = Dict[Any, Tuple[Optional[str], Optional[str]]]

# PREPARATION FOR ALL TABLES
# Define a shared mapping for labels that are common to all tables
shared_mapping: AbbrToNameDef = {
    'BMI': ('Body Mass Index', 'Measure of body fat based on height and weight that applies to adult men and women'),
    'Sex_1': ('Gender', 'Categorical variable, 1=Male, 0=Female')
}

# TABLE 0:
df0 = pd.read_pickle('table_0.pkl')

# RENAME ROWS AND COLUMNS
mapping0 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df0, k)) 
mapping0 |= {
    'Mean Diabetes': ('Mean Diabetes', None),
    'Std Diabetes': ('Std. Diabetes', None),
    'Mean PhysActivity': ('Mean Phys. Activity', None),
    'Std PhysActivity': ('Std. Phys. Activity', None),
    'Mean BMI': ('Mean BMI', None),
    'Std BMI': ('Std. BMI', None),
}

abbrs_to_names0, legend0 = split_mapping(mapping0)
df0 = df0.rename(columns=abbrs_to_names0, index=abbrs_to_names0)

# Transpose the table to make it narrower
df0 = df0.T

# SAVE AS LATEX:
to_latex_with_note(
    df0, 'table_0.tex',
    caption="Descriptive Statistics of Main Binary Variables and Body Mass Index Stratified by Gender", 
    label='table:DescriptiveStatistics',
    note="Descriptive statistics include mean and standard deviation of diabetes measure, physical activity, and body mass index.",
    legend=legend0)


# TABLE 1:
df1 = pd.read_pickle('table_1.pkl')

# RENAME ROWS AND COLUMNS
mapping1 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df1, k)) 
mapping1 |= {
    'coef': ('Coefficient', None),
    'p-value': ('P-value', None),
    'conf_int_low': ('CI (Lower)', None),
    'conf_int_high': ('CI (Higher)', None),
    'PhysActivity': ('Phys. Activity', 'Physical activity in the past 30 days'),
    'Intercept': ('Intercept', None),
    'Sex_1[T.True]': ('Gender Male', 'Categorical variable, Male'),
}

abbrs_to_names1, legend1 = split_mapping(mapping1)
df1 = df1.rename(columns=abbrs_to_names1, index=abbrs_to_names1)

# SAVE AS LATEX:
to_latex_with_note(
    df1, 'table_1.tex',
    caption='Multiple Linear Regression for Testing Association between Physical Activity Level and Diabetes, Adjusted by Age, Gender, and Body Mass Index', 
    label='table:LinearRegression',
    note='Table includes the results of a multiple linear regression model on the relationship between diabetes and physical activity, adjusted by gender, age, and body mass index.',
    legend=legend1)

