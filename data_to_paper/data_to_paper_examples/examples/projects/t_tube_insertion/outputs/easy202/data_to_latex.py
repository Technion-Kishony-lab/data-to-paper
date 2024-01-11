

# IMPORT
import pandas as pd
from typing import Dict, Any, Tuple, Optional
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES

shared_mapping: AbbrToNameDef = {
 'sex': ('Sex', 'Patient sex (0: Female, 1: Male)'),
 'age_c': ('Age', 'Patient age (years, rounded to half years)'),
 'wt': ('Weight', 'Patient weight (KG)'),
 'ht': ('Height', 'Patient height (CM)'),
 'RF': ('Random Forest', None),
 'EN': ('Elastic Net', None),
}

# TABLE 1:
df = pd.read_pickle('table_1.pkl')

# Transpose the dataframe to make the table narrower
df = df.T

# RENAME ROWS AND COLUMNS 
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)} 
mapping |= {
 'RF_Mean_Squared_Residuals': ('RF Mean Residuals', None),
 'RF_Std_Squared_Residuals': ('RF Std Residuals', None),
 'EN_Mean_Squared_Residuals': ('EN Mean Residuals', None),
 'EN_Std_Squared_Residuals': ('EN Std Residuals', None),
}
abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(index=abbrs_to_names)

# Save as latex:
to_latex_with_note(
 df, 'table_1.tex',
 caption="Mean and Standard Deviation of Squared residuals of the Random Forest model and the Elastic Net model", 
 label='table:rf_en_residuals',
 note='This table provides the mean and std dev of squared residuals for the Random Forest and Elastic Net models.',
 legend=legend)

# TABLE 2:
df = pd.read_pickle('table_2.pkl')

# RENAME ROWS AND COLUMNS
mapping = {
 't_stat': ('T-statistic', None),
 'p_value': ('P-value', None),
}
abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# FORMAT VALUES
df['P-value'] = df['P-value'].apply(format_p_value)

# Save as latex:
to_latex_with_note(
 df, 'table_2.tex',
 caption="Paired t-test results between means of Random Forest and Elastic Net squared residuals", 
 label='table:t_test_results',
 note='This table provides the T-statistic and P-value for the paired t-test comparing the means of squared residuals for the Random Forest and Elastic Net models.',
 legend=legend)

