
# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
    'mse': ('Mean Squared Error', 'Performance measure for regression tasks'),
}


# TABLE 1

df = pd.read_pickle('table_1.pkl')

# RENAME ROWS AND COLUMNS
mapping: AbbrToNameDef = shared_mapping.copy()
mapping.update({
    'Age Formula-Based Model': ('Age Formula Measure', None),
    'Height Formula-Based Model': ('Height Formula Measure', None),
    'ID Formula-Based Model': ('Tube ID Formula Measure', None),
    'ML Model': ('Best Machine Learning Model', None),
})

abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(df, 'table_1.tex',
                   caption="Comparison of Mean Squared Error between Machine Learning Model and Formula-Based Models", 
                   label='table:comparison_of_mse',
                   note=None,
                   legend=legend)


# TABLE 2

df = pd.read_pickle('table_2.pkl')

# FORMAT VALUES 
df['p_val'] = df['p_val'].apply(format_p_value)

# RENAME ROWS AND COLUMNS
mapping: AbbrToNameDef = {
    'model_pair': ('Comparison of Models', None),
    'Pair 1': ('Comparison Pair 1', None),
    'Pair 2': ('Comparison Pair 2', None),
    'Pair 3': ('Comparison Pair 3', None),
    't_stat': ('T-Statistic', "Measure used in hypothesis testing"),
    'p_val': ('P-value', "Determines the significance of results"),
}

abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(df, 'table_2.tex',
                   caption="Paired T-Statistic and P-Value for Comparison of Models",
                   label='table:model_comparison',
                   note=None,
                   legend=legend)
