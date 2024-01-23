
# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES

shared_mapping: AbbrToNameDef = {
 'sex' : ('Sex', 'Patient sex (0: Female, 1: Male)'),
 'age_c' : ('Age', 'Patient age in years, rounded to half years'),
 'ht' : ('Height', 'Patient height in centimeters'),
 'wt': ('Weight', 'Patient weight in kilograms'),
 'tube': ('Tube ID', 'Diameter, in mm, of the internal tube'),
 'tube_depth_G': ('OTTD', 'Optimal Tracheal Tube Depth, as determined by chest X-ray, in centimeters')
}

# TABLE 1:
df = pd.read_pickle('table_1.pkl')

# RENAME ROWS AND COLUMNS 
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)} 
mapping |= {
 'MSE': ('Mean Squared Error', None),
 'Model 1': ('Model 1 (Random Forest)', None),
 'Model 2': ('Model 2 (Elastic Net)', None),
 'Model 3': ('Model 3 (SVM)', None),
 'Model 4': ('Model 4 (Neural Network)', None),
 'Model 5': ('Model 5 (Height Formula)', None),
 'Model 6': ('Model 6 (Age Formula)', None),
 'Model 7': ('Model 7 (ID Formula)', None),
}
abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(
 df, 'table_1.tex',
 caption="Comparison of Mean Squared Error of Machine Learning Models and Formula-Based Models", 
 label='table:model_comparison',
 note="Details of the estimation methods of the models are found in the methods section",
 legend=legend)

# TABLE 2:
df = pd.read_pickle('table_2.pkl')

# RENAME ROWS AND COLUMNS 
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)} 
mapping |= {
 'ML Model 1': ('ML Model 1 (Random Forest)', None),
 'ML Model 2': ('ML Model 2 (Elastic Net)', None),
 'ML Model 3': ('ML Model 3 (SVM)', None),
 'ML Model 4': ('ML Model 4 (Neural Network)', None),
}

abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# FORMAT VALUES 
df['p-value'] = df['p-value'].apply(format_p_value)

# Update legend with abbreviation
legend.update({'ML Model': 'Machine Learning Model'})

# Save as Latex:
to_latex_with_note(
 df, 'table_2.tex',
 caption="Pairwise Comparison of Machine Learning Models and Height-based Formula Model", 
 label='table:model_t_test',
 note="Comparisons made by t-test",
 legend=legend)
