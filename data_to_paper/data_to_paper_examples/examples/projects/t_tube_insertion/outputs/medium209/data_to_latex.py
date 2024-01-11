
# IMPORT
import pandas as pd
from typing import Dict, Any, Optional, Tuple
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES

shared_mapping: AbbrToNameDef = {
 'sex': ('Gender', 'Patient sex, 0: Female, 1: Male'),
 'age_c': ('Age (Years)', 'Patient age, years rounded to half years'),
 'ht': ('Height (cm)', 'Patient height, cm'),
 'wt': ('Weight (kg)', 'Patient weight, kg'),
 'MSE': ('Mean Squared Error (MSE)', 'Measure of predictive performance of the model'),
}

# TABLE 1:
df = pd.read_pickle('table_1.pkl')

# FORMAT VALUES
# Format P-values
df['p-value'] = df['p-value'].apply(format_p_value)

# RENAME ROWS AND COLUMNS
mapping: AbbrToNameDef = {
 k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)
}

mapping |= {
 'p-value': ('P-value', 'P-value of the test for a difference in MSE between models'),
 'RF Model': ('Random Forest (RF) Model', 'Machine-learning model trained using the Random Forest algorithm'),
 'Formula-Based Model': ('Height Formula-Based Model', 'Model based on height formula: OTTD = height (cm) / 10 + 5 cm')
}

abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex
to_latex_with_note(
  df, 'table_1.tex',
  caption="Comparison of Predictive Performance of Machine-Learning Model and Height Formula-Based Model", 
  label='table:comparison_of_prediction_models',
  note="This table compares the predictive performance, as measured by the Mean Squared Error (MSE), of a Random Forest machine-learning model and a model based on the formula OTTD = height (cm) / 10 + 5, where OTTD refers to the optimal tracheal tube depth.", 
  legend=legend
)
