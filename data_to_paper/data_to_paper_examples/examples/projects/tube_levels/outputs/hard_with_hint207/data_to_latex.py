
# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
# Define shared mapping commonly used to rename columns and rows
shared_mapping: AbbrToNameDef = {
    'sex_1': ('Male', '1: Male, 0: Female'),
    'age_c': ('Age (years)', 'Patient age, years'),
    'ht': ('Height (cm)', 'Patient height, cm'),
    'wt': ('Weight (kg)', 'Patient weight, kg'),
    'tube': ('Tube ID (mm)', 'Internal diameter of the tracheal tube, mm'),
    'tube_depth_G': ('Optimal Tracheal Tube Depth (cm)', 'Determined by chest X-ray'),
}

# TABLE 1:
df1 = pd.read_pickle('table_1.pkl')

# FORMAT VALUES
# Format the p Value column
df1['p Value'] = df1['p Value'].apply(format_p_value)

# RENAME ROWS AND COLUMNS
# Define a table-specific dictionary mapping, mapping1, for labels in Table 1
mapping1 = {k: v for k, v in shared_mapping.items() if is_str_in_df(df1, k)} 
mapping1 |= {
 'Model Comparison': ('Model Comparison', "Comparison of the predictive power of machine learning and formula-based models"),
 'F Value': ('F Value', 'Value of the F-statistic from one-way ANOVA'),
 'p Value': ('p Value', 'Corresponding p-value from one-way ANOVA'),
}

# Split the mapping into renaming rules and legend entries
abbrs_to_names1, legend1 = split_mapping(mapping1)

# Rename the columns/rows in Table 1
df1 = df1.rename(columns=abbrs_to_names1, index=abbrs_to_names1)

# Save dataframe df1 as a latex table in 'table_1.tex'
to_latex_with_note(df1, 'table_1.tex',
                   caption="Comparison of Squared Residuals of Machine Learning Models and Formula-Based Models",
                   label='table:Comparison',
                   note="The table compares the squared residuals (prediction minus target squared) \
                   of different Machine Learning and Formula-Based Models. The F Value \
                   and p-value from one-way ANOVA are shown.",
                   legend=legend1)
