
# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping

# PREPARATION FOR ALL TABLES
shared_mapping = {
 'ht': ('Height', 'Measured in centimeters'),
 'age_c': ('Age', 'Measured in years'),
 'sex': ('Sex', '0:Female, 1:Male'),
 'std': ('Std. Dev.', None),
 'mean': ('Mean', None)
}

# TABLE 0:
df = pd.read_pickle('table_0.pkl')
df.columns.names = ['Params', 'Stats']
df.index.names = ['Gender']

mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)}
mapping |= {
 '0-Female': ('Female', None),
 '1-Male': ('Male', None)
}
abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(
df, 'table_0.tex',
caption="Descriptive stats of Height and Age separated by Sex", 
label='table:desc_stat_sex',
note="Table represents mean and std. dev. of Age and Height for both sexes.",
legend=legend)

# TABLE 1:
df = pd.read_pickle('table_1.pkl')

# FORMAT VALUES
df['p-value'] = df['p-value'].apply(format_p_value)
df = df.T

# RENAME ROWS AND COLUMNS
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)} 
mapping |= {
'RandomForest_mean_residual': ('RF Mean Res.', None),
'RandomForest_std_residual': ('RF Std. Dev. Res.', None),
'ElasticNet_mean_residual': ('EN Mean Res.', None),
'ElasticNet_std_residual': ('EN Std. Dev. Res.', None),
't-statistic': ('T-stat', None),
'p-value': ('P-value', None)
}
abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(
df, 'table_1.tex',
caption="Comparison of Squared Residuals from RF and EN Models", 
label='table:comp_residuals',
note="Table represents the comparison of Squared Residuals from RF and EN Models, including T-Statistic and P-value",
legend=legend)

# TABLE 2:
df = pd.read_pickle('table_2.pkl')
df.columns.names = ['Stats']
df.index.names = ['Result']

# FORMAT VALUES
df['p-value'] = df['p-value'].apply(format_p_value)

# RENAME ROWS AND COLUMNS
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)} 
mapping |= {
'z-statistic': ('Z-stat', None),
'p-value': ('P-value', None),
}
abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(
df, 'table_2.tex',
caption="Wilcoxon Signed-rank Test on Squared Residuals from RF and EN Models", 
label='table:wilcoxon_test',
note="Table represents the result of Wilcoxon Signed-rank Test on Squared Residuals from RF and EN Models",
legend=legend)
