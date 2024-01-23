
# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping
from typing import Dict, Any, Tuple, Optional

AbbrToNameDef = Dict[Any, Tuple[Optional[str], Optional[str]]]

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
    'mean_squared_residuals': ("Mean ResSq.", "Mean of Squared residuals"),
    'std_dev_squared_residuals': ("Std ResSq.", "Standard Deviation of Squared residuals"),
    '95% CI_squared_residuals': ('95% CI ResSq.', "95% Confidence Interval for the Mean of Squared residuals"),
    'p_value': ('P-value', None)
}

# TABLE 1:
df1 = pd.read_pickle('table_1.pkl')

# FORMAT VALUES
df1['p_value'] = df1['p_value'].apply(format_p_value)

# RENAME ROWS AND COLUMNS
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df1, k)} 

abbrs_to_names, names_to_definitions = split_mapping(mapping)

df1.rename(index=abbrs_to_names, columns=abbrs_to_names, inplace=True)

# Save as latex:
to_latex_with_note(
    df1, 
    'table_1.tex', 
    caption='Comparison of predictive powers of Machine Learning Model and Formula-Based Model.', 
    label='table:comparison_of_predictive_powers', 
    note=
    """
    The Mean ResSq. shows the average squared residuals of the models. 
    The lower value represents a better model. 
    The 95% CI ResSq. is the 95% Confidence Interval for the Mean ResSq.
    The P-value shows the statistical significance of the results. A P-value of less than 0.05 typically indicates a statistically significant result.
    """, 
    legend=names_to_definitions)
