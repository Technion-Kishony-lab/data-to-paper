

# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
 'RF': ('RF', 'Random Forest'),
 'EN': ('EN', 'Elastic Net'),
 'SVM': ('SVM', 'Support Vector Machine'),
 'NN': ('NN', 'Neural Network'),
 'HF': ('HF-M', 'Height Formula-based Model'),
 'AF': ('AF-M', 'Age Formula-based Model'),
 'IDF': ('IDF-M', 'ID Formula-based Model'),
}

# TABLE 1:
df1 = pd.read_pickle('table_1.pkl')

# RENAME ROWS AND COLUMNS 
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df1, k)}
mapping |= {
 'MSE': ('MSE', 'Mean Square Error'),
}

abbrs_to_names, legend = split_mapping(mapping)
df1 = df1.rename(columns=abbrs_to_names, index=abbrs_to_names)
df1 = df1.T

# Save as latex:
to_latex_with_note(df1, 'table_1.tex',
                   caption="Mean squared residuals for each model", 
                   label='table:msr_models',
                   legend=legend)

# TABLE 2:
df2 = pd.read_pickle('table_2.pkl')

# FORMAT VALUES
df2['p_value'] = df2['p_value'].apply(format_p_value)

# RENAME COLUMNS AND INDEX
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df2, k)}
mapping |= {
 'p_value': ('P-value', None),
 'ML Model': ('Model', None),
 'Test_0': ('Test 1', 'Random Forest Vs Height Formula-based Model'),
 'Test_1': ('Test 2', 'Random Forest Vs Age Formula-based Model'),
 'Test_2': ('Test 3', 'Random Forest Vs ID Formula-based Model'),
 'Test_3': ('Test 4', 'Elastic Net Vs Height Formula-based Model'),
 'Test_4': ('Test 5', 'Elastic Net Vs Age Formula-based Model'),
 'Test_5': ('Test 6', 'Elastic Net Vs ID Formula-based Model'),
 'Test_6': ('Test 7', 'Support Vector Machine Vs Height Formula-based Model'),
 'Test_7': ('Test 8', 'Support Vector Machine Vs Age Formula-based Model'),
 'Test_8': ('Test 9', 'Support Vector Machine Vs ID Formula-based Model'),
 'Test_9': ('Test 10', 'Neural Network Vs Height Formula-based Model'),
 'Test_10': ('Test 11', 'Neural Network Vs Age Formula-based Model'),
 'Test_11': ('Test 12', 'Neural Network Vs ID Formula-based Model'),
}

abbrs_to_names, legend = split_mapping(mapping)

df2 = df2.rename(columns=abbrs_to_names)
df2.rename(index=lambda s: abbrs_to_names.get(s, s), inplace=True)

# Save as latex:
to_latex_with_note(df2, 'table_2.tex', 
                   caption="Paired t-test results between each ML model and formula-based model",  
                   label='table:t_test_ml_formula', 
                   legend=legend)

