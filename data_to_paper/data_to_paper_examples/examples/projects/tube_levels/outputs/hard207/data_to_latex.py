
# IMPORT
import pandas as pd
from typing import Dict, Optional, Any, Tuple
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping

# Type of the data mapping
AbbrToNameDef = Dict[Any, Tuple[Optional[str], Optional[str]]]

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
 'age_c': ('AvgAge', 'Average age, years'),
 'sex': ('Sex', '0: female, 1: male'),
 'ht': ('Height', 'Height in cm'),
 'wt': ('Weight', 'Weight in kg'),
 'mean': (None, None),
 'std': (None, None),
}

# TABLE 0:
df = pd.read_pickle('table_0.pkl')

# RENAME ROWS AND COLUMNS
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)}
abbrs_to_names, legend = split_mapping(mapping)
df.rename(columns=abbrs_to_names, level=0, inplace=True)
df.rename(index=abbrs_to_names, inplace=True)

# Save as latex:
to_latex_with_note(
 df, 'table_0.tex',
 caption="Descriptive statistics of age and height stratified by sex", 
 label='table:desc_stats_age_height',
 legend=legend)

# TABLE 1:
df = pd.read_pickle('table_1.pkl')

# RENAME ROWS AND COLUMNS
mapping = {
 'Mean Squared Error': ('MSE', 'Mean Squared Error'),
}
abbrs_to_names, legend = split_mapping(mapping)
df.rename(columns=abbrs_to_names, inplace=True)

# Save as latex:
to_latex_with_note(
 df, 'table_1.tex',
 caption="Overall Performance of Machine Learning Models", 
 label='table:ml_model_perf',
 legend=legend)

# TABLE 2:
df = pd.read_pickle('table_2.pkl')

# RENAME ROWS AND COLUMNS
mapping = {
 'Mean Squared Error': ('MSE', 'Mean Squared Error'),
}
abbrs_to_names, legend = split_mapping(mapping)
df.rename(columns=abbrs_to_names, inplace=True)

# Save as latex:
to_latex_with_note(
 df, 'table_2.tex',
 caption="Overall Performance of Formula-Based Models", 
 label='table:formula_model_perf',
 legend=legend)

# TABLE 3:
df = pd.read_pickle('table_3.pkl')

# FORMAT VALUES
df['p-value'] = df['p-value'].apply(format_p_value)

# RENAME ROWS AND COLUMNS 
mapping = {
 't-statistic': ('TStat', 'T-Statistic of Independent t-test'),
 'p-value': ('PVal', 'P-Value of Independent t-test'),
 'ML models vs Formula-based models': ('Models', 'Comparison of ML models with Formula-based models'),
}
abbrs_to_names, legend = split_mapping(mapping)
df.rename(columns=abbrs_to_names, inplace=True)
df.rename(index=abbrs_to_names, inplace=True)

# Save as latex:
to_latex_with_note(
 df, 'table_3.tex',
 caption="Independent t-test: Comparison of ML models vs Formula-Based models", 
 label='table:ttest_ml_formula',
 legend=legend)
