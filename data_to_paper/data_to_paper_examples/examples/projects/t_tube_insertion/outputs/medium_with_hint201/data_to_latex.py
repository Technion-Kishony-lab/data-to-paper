
# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES

shared_mapping: AbbrToNameDef = {
    'sex': ('Sex', 'Sex of patient (0=female, 1=male)'),
    'age_c': ('Age (years)', 'Patient age, years, rounded to half years'),
    'ht': ('Height (cm)', 'Patient height, cm'),
    'Mean Squared Error': ('Mean Squared Error', 'Mean Squared Error between the predicted and actual values')
}

# TABLE 0:
df_0 = pd.read_pickle('table_0.pkl')

# RENAME ROWS AND COLUMNS
mapping_0 = {k: v for k, v in shared_mapping.items() if is_str_in_df(df_0, k)}
abbrs_to_names_0, legend_0 = split_mapping(mapping_0)
df_0 = df_0.rename(columns=abbrs_to_names_0, index=abbrs_to_names_0)

# Save as latex
to_latex_with_note(
    df_0, 'table_0.tex',
    caption="Descriptive statistics of height and age stratified by sex",
    label='table:table_0',
    note="All values are means and standard deviations. Sex is denoted as 'female' and 'male'. Age is in years, rounded to half years. Height is measured in cm.",
    legend=legend_0
)

# TABLE 1:
df_1 = pd.read_pickle('table_1.pkl')

# FORMAT VALUES
df_1['P-value'] = df_1['P-value'].apply(format_p_value)

# RENAME ROWS AND COLUMNS
mapping_1 = {k: v for k, v in shared_mapping.items() if is_str_in_df(df_1, k)}
mapping_1 |= {
    'T-Test Statistic': ('T-statistic', 'T-test statistic from pair t-test between the squared errors of the two models'),
    'P-value': ('P-value', 'P-value from paired t-test'),
}
abbrs_to_names_1, legend_1 = split_mapping(mapping_1)
df_1 = df_1.rename(columns=abbrs_to_names_1)

# Save as latex
to_latex_with_note(
    df_1, 'table_1.tex',
    caption="Comparison of prediction errors from Random Forest model and a formula-based model",
    label='table:table_1',
    note=None,
    legend=legend_1
)
