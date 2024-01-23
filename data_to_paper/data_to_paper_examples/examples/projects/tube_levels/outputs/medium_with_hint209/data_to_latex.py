
# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef
from typing import Dict, Tuple, Optional, Any

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
 'sex': ('Gend.', 'Patients\' gender, 0: female, 1: male'),
 'age_c': ('Age (Yrs)', None),
 'ht': ('Height (cm)', None),
 'wt': ('Weight (kg)', None),
 'tube_depth_G': ('OTTD (cm)', 'Measured by chest X-ray'),
 'gender': (None, '0: female, 1: male'),
 'statistic': (None, 'Describe method applied to each attribute per gender'),
 'RF Model': (None, 'Random Forest model')
}

# TABLE 0:
df = pd.read_pickle('table_0.pkl')

mapping_0 = {k: v for k, v in shared_mapping.items() if is_str_in_df(df, k)}

# Splitting the map into column names and legend
abbrs_to_names, legend = split_mapping(mapping_0)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as Latex
to_latex_with_note(df, 'table_0.tex',
                   caption="Descriptive statistics of age, height, weight, and optimal tracheal tube depth stratified by gender.", 
                   label='table:desc_stats_gender',
                   note=None,
                   legend=legend)

# TABLE 1:
df = pd.read_pickle('table_1.pkl')

# Change the full dictionary to a shortened format for fitting into the LaTeX table
df["Best parameters of RF model"] = df["Best parameters of RF model"].apply(lambda x: 'max_depth=10, min_samples_leaf=2, min_samples_split=2, n_estimators=100')

mapping_1 = {"Best parameters of RF model": ("Best Params of RF", "Optimal hyperparameters found for the Random Forest model")}
mapping_1.update({"RF Model": shared_mapping["RF Model"]})
# Splitting the map into column names and legend
abbrs_to_names, legend = split_mapping(mapping_1)

df = df.rename(index={'ML Model': 'RF Model'}, columns=abbrs_to_names)

# Save as Latex
to_latex_with_note(df, 'table_1.tex',
                   caption="Best Parameters of RF Model.", 
                   label='table:RF_params',
                   note=None,
                   legend=legend)

# TABLE 2:
df = pd.read_pickle('table_2.pkl')

mapping_2 = {
    "intercept": ("Int.", "Intercept for the height formula-based model."),
    "coefficient of height": ("Coeff. of Height", "Coefficient for height for the height formula-based model.")}
abbrs_to_names, legend = split_mapping(mapping_2)
df = df.rename(columns=abbrs_to_names)

# Save as Latex
to_latex_with_note(df, 'table_2.tex',
                   caption="Coefficients for Height Formula-Based Model.", 
                   label='table:height_formula_params',
                   note=None,
                   legend=legend)

# TABLE 3:
df = pd.read_pickle('table_3.pkl')

# FORMAT VALUES
df['p_val'] = df['p_val'].apply(format_p_value)

mapping_3 = {
    "mean_squared_residuals": ("MS Residuals", "Mean Squared Residuals"),
    "std_squared_residuals": ("STD of Sq. Residuals", "Standard deviation of squared residuals"),
    "t_stat": ("T-Stat", "T-statistic of the paired t-test"),
    "p_val": ("P-Value", "P-value of the paired t-test"),}
mapping_3.update({"RF Model": shared_mapping["RF Model"]})
abbrs_to_names, legend = split_mapping(mapping_3)
df = df.rename(columns=abbrs_to_names)

# Save as Latex
to_latex_with_note(df, 'table_3.tex',
                   caption="Hypothesis Testing: Comparing The Mean Squared Residuals of Random Forest Model and Formula-Based Model", 
                   label='table:hypothesis_testing',
                   note=None,
                   legend=legend)
