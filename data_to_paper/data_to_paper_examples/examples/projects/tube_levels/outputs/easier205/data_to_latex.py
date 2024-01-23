
# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
    'ht': ('Height', 'Patient Height in cm'),
    'age_c': ('Age', 'Patient Age in years, rounded to half years'),
    'sex': ('Sex', 'Patient Sex: 0=Female, 1=Male'),
    'wt': ('Weight', 'Patient Weight in kg')
}

# TABLE 0:
df0 = pd.read_pickle('table_0.pkl')

# RENAME ROWS AND COLUMNS
mapping_table0 = {k: v for k, v in shared_mapping.items() if is_str_in_df(df0, k)} 
for old_name, (new_name, definition) in mapping_table0.items():
    if old_name in df0.columns.get_level_values(0):
        df0.rename(columns={old_name: new_name}, level=0, inplace=True)
abbrs_to_names, legend = split_mapping(mapping_table0)

# Save as latex:
to_latex_with_note(
    df0, 'table_0.tex',
    caption="Descriptive statistics of height and age, stratified by sex", 
    label='table:descriptive_sex',
    note="Here Age and Height are depicted with mean, standard deviation, and count, stratified by sex.",
    legend=legend)

# TABLE 1:
df1 = pd.read_pickle('table_1.pkl')

# Save as latex:
to_latex_with_note(
    df1, 'table_1.tex',
    caption="Comparison of Mean Squared Errors from Height and Age-Based Models", 
    label='table:MSE_comparison',
    note="This table compares the Mean Squared Errors of the models based on height and age.",
    legend={'MSE':'Mean Squared Error'})

# TABLE 2:
df2 = pd.read_pickle('table_2.pkl')

# FORMAT VALUES
df2.loc['p-value'] = df2.loc['p-value'].apply(format_p_value)

# Save as latex:
to_latex_with_note(
    df2, 'table_2.tex',
    caption="Statistical Comparison of Residuals of the Height and Age Formula-Based Models", 
    label='table:statistical_comparison_res',
    note="This table provides a statistical comparison of residuals.")
