
# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
# Mapping of column names common to all tables
shared_mapping: AbbrToNameDef = {
    'ht': ('Height','Participant height, cm'),
    'age_c': ('Age', 'Participant age, years'),
    'wt': ('Weight', 'Participant weight, kg'),
}

# TABLE 1
df = pd.read_pickle('table_1.pkl')

# FORMAT VALUES
# P-values formatting
df = df.applymap(format_p_value)

# RENAME ROWS AND COLUMNS
# Combine shared mappings with table specific mappings
table_1_mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)}
table_1_mapping |= {
    'Random Forest': ('RF', 'Random Forest Model'),
    'Elastic Net': ('EN', 'Elastic Net Model'),
    'Support Vector Machine': ('SVM', 'Support Vector Machine Model'),
    'Neural Network': ('NN', 'Neural Network Model'),
    'Height Formula': ('HF', 'Height Formula-based Model'),
    'Age Formula': ('AF', 'Age Formula-based Model'),
    'ID Formula': ('IF', 'ID Formula-based Model')
}
abbrs_to_names, legend = split_mapping(table_1_mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save to latex
to_latex_with_note(df, 'table_1.tex',
                   caption="P-values of paired t-tests between Machine Learning models and Formula-based models for Optimal Tracheal Tube Depth", 
                   label='table:ComparisonModels',
                   note="",
                   legend=legend)
