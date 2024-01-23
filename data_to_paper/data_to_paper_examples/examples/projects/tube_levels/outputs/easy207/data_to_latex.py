
# IMPORT
import pandas as pd
from typing import Dict, Optional, Tuple
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
 'age_c': ('Age', 'Age in years, rounded to half years'),
 'ht': ('Ht', 'Height in cm'),
 'sex': ('Sex', 'Patient sex (0=female, 1=male)'),
 'tube_depth_G': ('Depth', 'Optimal tracheal tube depth as determined by chest X-ray in cm'),
 'RF': ('Random Forest', 'Machine learning model'),
 'EN': ('Elastic Net', 'Machine learning model')
}

# TABLE 0
df = pd.read_pickle('table_0.pkl')

# RENAME ROWS AND COLUMNS
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)} 

abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as LaTeX:
to_latex_with_note(
 df, 'table_0.tex',
 caption="Descriptive statistics for male and female patients", 
 label='table:table0',
 note="The table provides the count, mean, standard deviation, minimum, 25th, 50th and 75th percentiles, and maximum of the patients' age and height stratified by sex",
 legend=legend)

# TABLE 1
df = pd.read_pickle('table_1.pkl')

# FORMAT VALUES
df["P-value"] = df["P-value"].apply(format_p_value)

# RENAME COLUMNS
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)}
mapping |= {
 'Best Parameters': ('Model Parameters', 'Best parameters obtained by GridSearchCV'),
 'Residual Mean': ('Res Mean', 'Mean of residuals (cm)'),
 'Residual STD': ('Res STD', 'STD of residuals (cm)'),
 'T-stat': ('T-Stat', 'T-statistic from paired t-test'),
 'P-value': ('P-value', 'P-value from paired t-test'),
}

abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names)
df = df.rename(index={'Random Forest':'RF', 'Elastic Net':'EN'})

# TRANSPOSE THE DATAFRAME
df = df.transpose()

# ADDITIONAL ELEMENTS FOR THE LEGEND
legend |= {'RF': 'Random Forest', 'EN': 'Elastic Net'}

# Save as LaTeX:
to_latex_with_note(
 df, 'table_1.tex',
 caption="Hyperparameter tuning and performance evaluation for RF and EN", 
 label='table:table1',
 note="Best parameters for each model are obtained by GridSearchCV. The mean and standard deviation of residuals, and the T-statistic and p-value from the paired students t-test are also reported",
 legend=legend
)

