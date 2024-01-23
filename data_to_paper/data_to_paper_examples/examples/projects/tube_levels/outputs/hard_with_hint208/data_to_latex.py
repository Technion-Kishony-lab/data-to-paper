

# IMPORT
import pandas as pd
from typing import Dict, Any, Tuple, Optional

from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES

# define a shared mapping for labels that are common to all tables
shared_mapping: AbbrToNameDef = {
    'RF': ('Random Forest', None),
    'EN': ('Elastic Net', None),
    'SVM': ('Support Vector Machine', None),
    'NN': ('Neural Network', None),
    'Height': ('Height Model', 'Optimal tracheal tube depth using the Height Formula-based Model'),
    'Age': ('Age Model', 'Optimal tracheal tube depth using the Age Formula-based Model'),
    'ID': ('ID Model', 'Optimal tracheal tube depth using the ID Formula-based Model'),
    'P_Value': ('P-value', 'The significance level of the difference between the machine learning and formula-based models')
}

# TABLE 0:
df = pd.read_pickle('table_0.pkl')

# FORMAT VALUES 
df['P_Value'] = df['P_Value'].apply(format_p_value)

# RENAME ROWS AND COLUMNS 
# Getting labels relevant for the current dataframe from the shared mapping
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)} 

# Additional specific mapping for the current dataframe
mapping |= {
 'T_Statistic': ('T-Statistic', 'The statistic value resulted from T-test '),
}

abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(
    df, 'table_0.tex',
    caption="Comparison of Predictive Power of Machine Learning Models Vs. Formula-Based Models", 
    label='table:comparison_ml_formulas',
    note="Values represent the Squared Residuals (prediction - target)^2.",
    legend=legend)


# TABLE <?>:
# < same structure for other tables, if they exist > 

