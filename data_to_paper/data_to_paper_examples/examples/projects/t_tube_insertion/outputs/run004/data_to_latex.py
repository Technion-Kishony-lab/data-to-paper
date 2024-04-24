
# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
    'Mean_Squared_Error': ('MSE', 'Mean squared error'),
    'Std_Error': ('SE', 'Standard Error'),
    'Root_Mean_Squared_Error': ('RMSE', 'Root mean squared error'),
    'ML Model': ('ML Model', 'The machine learning model used'),
    'Formula Model': ('Formula Model', 'The formula based model used'),
    't-stat': ('t-statistic', 'Value of the t-statistic from the t-test'),
    'p-value': (None, 'The p-value of the significance test'),
    'ML_SVM': ('ML Support Vector Machine', None),
    'ML_Elastic Net': ('ML ElasticNet', 'The Machine Learning Model ElasticNet'),
    'ML_Neural Network': ('ML Neural Network', None),
    'ML_Random Forest': ('ML Random Forest', None),
    'Formula_Age': ('Formula Age', None),
    'Formula_Height': ('Formula Height', None),
    'Formula_ID': ('Formula ID', 'Formula based on tube ID'),
    'Test_0': ('Test 0', 'Comparison of Random Forest to Height-Model'),
    'Test_1': ('Test 1', 'Comparison of Random Forest to Age-Model'),
    'Test_10': ('Test 10', 'Comparison of Neural Network to Age-Model'),
    'Test_11': ('Test 11', 'Comparison of Neural Network to ID-Model'),
    'Test_2': ('Test 2', 'Comparison of Random Forest to ID-Model'),
    'Test_3': ('Test 3', 'Comparison of ElasticNet to Height-Model'),
    'Test_4': ('Test 4', 'Comparison of ElasticNet to Age-Model'),
    'Test_5': ('Test 5', 'Comparison of ElasticNet to ID-Model'),
    'Test_6': ('Test 6', 'Comparison of Support Vector Machine to Height-Model'),
    'Test_7': ('Test 7', 'Comparison of Support Vector Machine to Age-Model'),
    'Test_8': ('Test 8', 'Comparison of Support Vector Machine to ID-Model'),
    'Test_9': ('Test 9', 'Comparison of Neural Network to Height-Model')
}

# TABLE 1:
df1 = pd.read_pickle('table_1.pkl')

mapping1 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df1, k)) 
abbrs_to_names1, legend1 = split_mapping(mapping1)
df1 = df1.rename(columns=abbrs_to_names1, index=abbrs_to_names1)

# SAVE AS LATEX:
to_latex_with_note(
    df1, 'table_1.tex',
    caption="Machine learning models performance comparison.", 
    label='table:ML_Model_Performance',
    note='',
    legend=legend1
)

# TABLE 2:
df2 = pd.read_pickle('table_2.pkl')

mapping2 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df2, k)) 
abbrs_to_names2, legend2 = split_mapping(mapping2)
df2 = df2.rename(columns=abbrs_to_names2, index=abbrs_to_names2)

# SAVE AS LATEX:
to_latex_with_note(
    df2, 'table_2.tex', 
    caption="Formula based models performance comparison.", 
    label='table:Formula_Model_Performance',
    note='',
    legend=legend2
)

# TABLE 3:
df3 = pd.read_pickle('table_3.pkl')

mapping3 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df3, k)) 
abbrs_to_names3, legend3 = split_mapping(mapping3)
df3 = df3.rename(columns=abbrs_to_names3, index=abbrs_to_names3)

# SAVE AS LATEX:
to_latex_with_note(
    df3, 'table_3.tex',
    caption="Hypotheses testing comparison.", 
    label='table:ML_vs_Formula_Models',
    note="Each row of the table tests a given ML model against a given formula-based model",
    legend=legend3
)
