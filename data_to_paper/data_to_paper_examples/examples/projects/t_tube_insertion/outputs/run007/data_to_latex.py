

# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
    'id_model': ('Tube ID model', 'Prediction model based on tube inner diameter'),
    'height_model': ('Height model', 'Prediction model based on patient height'),
    'age_model': ('Age model', 'Prediction model based on patient age bracket'),
    'RandomForest': ('RF', 'Random Forest'),
    'ElasticNet': ('EN', 'Elastic Net'),
    'SupportVectorMachine': ('SVM', 'Support Vector Machine'),
    'NeuralNetwork': ('NN', 'Neural Network'),
}

# TABLE 1:
df1 = pd.read_pickle('table_1.pkl')

# RENAME ROWS AND COLUMNS 
mapping1 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df1, k))
abbrs_to_names1, legend1 = split_mapping(mapping1)
df1 = df1.rename(columns=abbrs_to_names1, index=abbrs_to_names1)

# SAVE AS LATEX:
to_latex_with_note(
    df1, 'table_1.tex',
    caption="Comparison of p-values between machine learning models and formula-based models",
    label='table:compare_pvalues',
    note="p-values are calculated using paired T-test on squared residuals between each machine learning model and each formula-based model, significant p-values are bolded. (*) : p-value < 0.05, (**) : p-value < 0.01",
    legend=legend1
)

# TABLE 2:
df2 = pd.read_pickle('table_2.pkl')

# RENAME ROWS AND COLUMNS 
mapping2 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df2, k)) 
abbrs_to_names2, legend2 = split_mapping(mapping2)
df2 = df2.rename(columns=abbrs_to_names2, index=abbrs_to_names2)

# SAVE AS LATEX:
to_latex_with_note(
    df2, 'table_2.tex',
    caption="Mean Squared Residuals for each model",
    label='table:mean_squared_residuals',
    note="Mean Squared Residuals are calculated on the same test set for all models",
    legend=legend2
)
