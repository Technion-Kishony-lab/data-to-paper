
# IMPORT
import pandas as pd
from typing import Dict, Any, Optional, Tuple
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES

# Shared mapping for all tables
shared_mapping: dict = {
    "sex": ("Sex", "0: Female, 1: Male"),
    "age_c": ("Age", "Age (years, rounded to half years)"),
    "wt": ("Weight", "Weight (kg)"),
    "ht": ("Height", "Height (cm)"),
    "tube_depth_G": ("OTTD", "Optimal Tracheal Tube Depth as determined by chest X-ray (cm)"),
    "R2_score": ("R2 Score", "Model's goodness-of-fit score"),
    "RMSE": ("RMSE", "Root Mean Square Error")
}


# TABLE 0
df0 = pd.read_pickle('table_0.pkl')

# TRANSPOSE THE DATAFRAME
df0 = df0.T

# RENAME ROWS AND COLUMNS
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df0, k)} 
mapping |= {
    "average_age": ("Avg Age", "Average of age (years, rounded to half years)"),
    "average_weight": ("Avg Wt", "Average of weight (kg)"),
    "standard_deviation_age": ("SD Age", None),
    "standard_deviation_weight": ("SD Weight", None),
}
abbrs_to_names, legend = split_mapping(mapping)
df0 = df0.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex
to_latex_with_note(
    df0, "table_0.tex",
    caption="Descriptive statistics of patient ages and weights stratified by their sex",
    label="table:desc_stats_age_weight_by_sex",
    legend=legend
) 


# TABLE 1
df1 = pd.read_pickle("table_1.pkl") 

# FORMAT VALUES
df1["p-value"] = df1["p-value"].apply(format_p_value)

# RENAME ROWS AND COLUMNS
mapping = {k: v for k, v in shared_mapping.items() if is_str_in_df(df1, k)}
mapping |= {
    "t-statistic": ("t-stat", None),
    "p-value": ("p-val", "Probabilities from t-test"),
}
abbrs_to_names, legend = split_mapping(mapping)
df1 = df1.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex
to_latex_with_note(
    df1,
    "table_1.tex",
    caption="Predictive Power of Machine Learning Models",
    label="table:pred_power_ml_models",
    legend=legend,
)
