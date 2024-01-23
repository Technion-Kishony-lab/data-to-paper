
# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping
from typing import Dict, Tuple, Any, Optional

# defining the alias for annotation -> AbbrToNameDef
AbbrToNameDef = Dict[Any, Tuple[Optional[str], Optional[str]]]

# PREPARATION FOR ALL TABLES
# shared_mapping: Mapping abbreviation to full names and definitions
shared_mapping: AbbrToNameDef = {
 'age_c': ('Age, years', None),
 'ht': ('Height, cm', None),
 'wt': ('Weight, kg', None), 
}

# TABLE 0:
# Load table
df0 = pd.read_pickle('table_0.pkl')
# RENAME ROWS AND COLUMNS
# Mapping for table 0
mapping_table_0: AbbrToNameDef = {
 **shared_mapping,
 'age_c_mean': ('Avg. Age', 'Average age, rounded to half years'),
 'age_c_std': ('Age Std. Dev', None),
 'ht_mean': ('Avg. Height', 'Average height (cm)'),
 'ht_std': ('Height Std. Dev', None),  
 }
 # Split Mapping
abbrs_to_names, legend = split_mapping(mapping_table_0)
# Rename
df0 = df0.rename(columns=abbrs_to_names, index=abbrs_to_names)
# Save as latex:
to_latex_with_note(
 df0, 'table_0.tex',
 caption="Summary statistics of age and height divided by sex", 
 label='table:T0',
 note="Sex is represented as 0: Female, 1: Male",
 legend=legend)

# TABLE 1:
# Load table
df1 = pd.read_pickle('table_1.pkl')
# FORMAT VALUES
df1['p_value'] = df1['p_value'].apply(format_p_value)
# RENAME ROWS AND COLUMNS
# Mapping for table 1
mapping_table_1: AbbrToNameDef = {
 'Model_1': ('Model 1: ElasticNet', None),
 'Model_2': ('Model 2: RandomForest', None),
 'Model_3': ('Model 3: SVM', None),
 'Model_4': ('Model 4: NeuralNetwork', None),
 'Mean_Squared_Error': ('Mean Squared Error (MSE)', 'Difference between the predicted OTTD by the model and the actual OTTD determined by chest X-ray'),
 'p_value': ('p-value', 'Probability that the null hypothesis (the model has predictive power equal to the mean squared error) is true')
 }
# Split Mapping
abbrs_to_names, legend = split_mapping(mapping_table_1)
# Rename
df1 = df1.rename(columns=abbrs_to_names, index=abbrs_to_names)
# Save as latex:
to_latex_with_note(df1, 'table_1.tex', 
                   caption="Comparison of predictive power of different models", 
                   label='table:T1', 
                   legend=legend)

