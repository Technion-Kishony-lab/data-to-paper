
# IMPORT
import pandas as pd
from typing import Dict, Any, Optional, Tuple
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping

# PREPARATION FOR ALL TABLES

# No shared mapping required as per data instructions

# TABLE 1:

df1 = pd.read_pickle('table_1.pkl')

# FORMAT VALUES
df1['p-value'] = df1['p-value'].apply(format_p_value)

# RENAME COLUMNS AND ROWS 
mapping: Dict[Any, Tuple[Optional[str], Optional[str]]] = {
 'p-value': ('P-value', None),
 'Comparison of Random Forest and Height Formula': ('RF vs Height Formula', None),
 'Comparison of Random Forest and Age Formula': ('RF vs Age Formula', None),
 'Comparison of Random Forest and Tube ID Formula': ('RF vs Tube ID Formula', None),
 'Comparison of Elastic Net and Height Formula': ('EN vs Height Formula', None),
 'Comparison of Elastic Net and Age Formula': ('EN vs Age Formula', None),
 'Comparison of Elastic Net and Tube ID Formula': ('EN vs Tube ID Formula', None),
 'Comparison of Support Vector Machine (SVM) and Height Formula': ('SVM vs Height Formula', None),
 'Comparison of Support Vector Machine (SVM) and Age Formula': ('SVM vs Age Formula', None),
 'Comparison of Support Vector Machine (SVM) and Tube ID Formula': ('SVM vs Tube ID Formula', None),
 'Comparison of Neural Network (NN) and Height Formula': ('NN vs Height Formula', None),
 'Comparison of Neural Network (NN) and Age Formula': ('NN vs Age Formula', None),
 'Comparison of Neural Network (NN) and Tube ID Formula': ('NN vs Tube ID Formula', None),
}

abbrs_to_names, legend = split_mapping(mapping)
df1 = df1.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(
 df1, 'table_1.tex',
 caption="Comparison of p-values from the paired t-test of squared residuals of different machine-learning models and formula-based models",
 label='table:comparison_models_formulas',
 note= None, 
 legend=legend
)
