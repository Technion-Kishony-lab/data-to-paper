
# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, is_str_in_df, split_mapping, AbbrToNameDef
from typing import Any, Dict, Optional, Tuple

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
    'sex': ('Sex', 'Patient Sex (0 = female, 1 = male)'),
    'age_c': ('Age', 'Patient age in years, rounded to half years'),
    'ht': ('Height', 'Patient height in cm'),
    'wt': ('Weight', 'Patient weight in kg'),
    'tube_depth_G': ('OTTD', 'Optimal tracheal tube depth as determined by chest X-ray in cm'),
}

# TABLE 1:
df1 = pd.read_pickle('table_1.pkl')

# FORMAT VALUES 
# No formatting of values needed in this table

# RENAME ROWS AND COLUMNS 
mapping1 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df1, k)) 
mapping1 |= {
    "Mean Squared Error": ("MSE", "Mean Squared Error"),
    't-statistic': ("t-statistic", None),
    'p-value': ("P-value", None),
}

abbrs_to_names1, legend1 = split_mapping(mapping1)
df1 = df1.rename(columns=abbrs_to_names1, index=abbrs_to_names1)

# SAVE AS LATEX
to_latex_with_note(
    df1, 'table_1.tex',
    caption="Comparison of performance between Machine Learning Model (Random Forest) and formula-based method", 
    label='table:comparison_of_ML_and_formula_based',
    note="Models evaluted by their Mean Squared Error (MSE) on the same test set",
    legend=legend1,
)


# TABLE 2:
df2 = pd.read_pickle('table_2.pkl')

# FORMAT VALUES 
# No formatting of values needed in this table

# RENAME ROWS AND COLUMNS 
mapping2 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df2, k)) 
mapping2 |= {
    'pearson_correlation': ("Pearson Coefficient", None),
    'p_value': ("P-value", None),
}

abbrs_to_names2, legend2 = split_mapping(mapping2)
df2 = df2.rename(columns=abbrs_to_names2, index=abbrs_to_names2)

# SAVE AS LATEX
to_latex_with_note(
    df2, 'table_2.tex',
    caption="Correlation between variables and the target variable", 
    label='table:correlation_to_target',
    note="Correlation values calculated using Pearson method",
    legend=legend2,
)


# TABLE 3:
df3 = pd.read_pickle('table_3.pkl')

# FORMAT VALUES 
# No formatting of values needed in this table

# RENAME ROWS AND COLUMNS 
mapping3 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df3, k)) 
mapping3 |= {
    'Importance': ("Importance", None),
    'Lower 95% CI': ('Lower 95%', 'Lower bound of 95% Confidence Interval'),
    'Upper 95% CI': ('Upper 95%', 'Upper bound of 95% Confidence Interval'),
}

abbrs_to_names3, legend3 = split_mapping(mapping3)
df3 = df3.rename(columns=abbrs_to_names3, index=abbrs_to_names3)

# SAVE AS LATEX
to_latex_with_note(
    df3, 'table_3.tex',
    caption="Feature importances from the Random Forest model, including confidence intervals", 
    label='table:feature_importances',
    note="Importances calculated base on feature contribution in Random Forest method",
    legend=legend3,
)
