
# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
    'sex_1': ('Male Gender', '1: Male, 0: Female'),
    'age_c': ('Age', 'Patient age in years, rounded to half years'),
    'ht': ('Height', 'Patient height in cm'),
    'wt': ('Weight', 'Patient weight in kg'),
    'tube_depth_G': ('OTTD', 'Optimal Tracheal Tube Depth as determined by chest X-ray in cm'),
}

# Table 1:
df1 = pd.read_pickle('table_1.pkl')

# RENAME ROWS AND COLUMNS
mapping1 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df1, k)) 
abbrs_to_names1, legend1 = split_mapping(mapping1)
df1.rename(columns=abbrs_to_names1, index=abbrs_to_names1, inplace=True)

# RENAMING AGAIN TO MAKE THE COLUMN NAMES SHORTER AND REMOVE UNALLOWED UNDERSCORE CHARACTER
replacement_dict = {
    "Mean_Squared_Residuals": "MSE",
    "Confidence_Interval_For_Mean_Squared_Residuals": "95% CI For MSE",
    'RF model': 'Random Forest (RF) Model',
    'Formula-based model': 'Formula-based Model'
}
df1.rename(columns=replacement_dict, index=replacement_dict, inplace=True)

# Updating the legend
legend1.update({
    'MSE': 'Mean Squared Error',
    'Random Forest (RF) Model': 'A Machine Learning model called Random Forest',
    'Formula-based Model': 'A model based on the formula OTTD = height [cm] / 10 + 5 cm'
})

# SAVE AS LATEX:
to_latex_with_note(
    df1, 'table_1.tex',
    caption="Comparison of Mean Squared Errors (MSE) between RandomForest (ML) model and Formula-based model", 
    label='table:ComparisonResiduals',
    note=None,
    legend=legend1
)
