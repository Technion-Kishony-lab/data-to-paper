

# IMPORT
import pandas as pd
from typing import Dict, Any, Tuple, Optional
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES

shared_mapping: AbbrToNameDef = {
    'sex': ('Sex', 'Patient Sex. 0: female, 1: male'),
    'age_c': ('Age', 'Patient age, years rounded to half years'),
    'ht': ('Height', 'Patient height, cm'),
    'wt': ('Weight', 'Patient weight, kg'),
    'tube_depth_G': ('OTTD', 'Optimal Tracheal Tube Depth, determined by chest X-ray, cm'),
    'rf_residual': ('RF Residuals', 'Squared residuals of the Random Forest model'),
    'formula_residual': ('Formula Residuals', 'Squared residuals of the Formula-based model')
}

# TABLE 1
df1 = pd.read_pickle('table_1.pkl')

mapping1 = {k: v for k, v in shared_mapping.items() if is_str_in_df(df1, k)}
mapping1 |= {
    'RF': ('Random Forest', 'Random Forest Model'),
    'Formula': ('Height Formula', 'Height Formula Model'),
    'Model': ('Model', 'Predictive Models'),
    'Mean squared residual': ('Mean SQD', 'Mean Squared Deviation'),
    'Standard deviation of residual': ('STD of SQD', 'Standard Deviation of Squared Deviation'),
}
abbrs_to_names1, legend1 = split_mapping(mapping1)
df1 = df1.rename(columns=abbrs_to_names1, index=abbrs_to_names1)

to_latex_with_note(
 df1, 'table_1.tex',
 caption="Comparison of prediction performance using Machine Learning model and formula-based model", 
 label='table:comp_pred_perf',
 note="",
 legend=legend1)

# TABLE 2
df2 = pd.read_pickle('table_2.pkl')

mapping2 = {k: v for k, v in shared_mapping.items() if is_str_in_df(df2, k)}
mapping2 |= {
    'Predicted OTTD (Random Forest)': ('OTTD (RF)', 'Predicted OTTD Using Random Forest Model, cm'),
    'Predicted OTTD (Height Formula)': ('OTTD (HF)', 'Predicted OTTD Using Height Formula, cm'),
    'Actual OTTD': ('OTTD', 'Optimal Tracheal Tube Depth, determined by chest X-ray, cm'),
    'Mean': ('Mean', 'Mean'),
    'Standard Deviation': ('Std Dev', 'Standard deviation'),
}
abbrs_to_names2, legend2 = split_mapping(mapping2)
df2 = df2.rename(columns=abbrs_to_names2, index=abbrs_to_names2)

# Transpose df2 so it fits the page layout better:
df2 = df2.T

to_latex_with_note(
 df2, 'table_2.tex',
 caption="Summary Statistics for Actual and Predicted OTTD for Both Models", 
 label='table:summary_stat',
 note="",
 legend=legend2)
