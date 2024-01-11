
# IMPORT
import pandas as pd
from typing import Dict, Any, Tuple, Optional
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
 'Comparison': ('Comparison', 'Comparison between machine learning models and formula-based models'),
 'Adjusted p-value': ('Adjusted p-value', 'P-value adjusted for multiple comparisons using the Bonferroni method')
}

# TABLE 1:
df1 = pd.read_pickle('table_1.pkl')

# FORMAT VALUES
df1['Adjusted p-value'] = df1['Adjusted p-value'].apply(format_p_value)

# RENAME ROWS AND COLUMNS 
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df1, k)}
mapping.update({label: (label, "Comparison between Machine Learning model and Formula-based model") for label in df1.index})
abbrs_to_names, legend = split_mapping(mapping)
df1 = df1.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(
 df1, 'table_1.tex',
 caption="Comparative Analysis between Machine Learning Models and Formula-Based Models", 
 label='table:ml_vs_formula',
 note="The table shows the comparison of the residuals' squared errors between Machine Learning models and Formula-Based models for predicting OTTD. The adjusted P-values reported were calculated using multiple pairwise comparisons with the Bonferroni adjustment.",
 legend=legend)

