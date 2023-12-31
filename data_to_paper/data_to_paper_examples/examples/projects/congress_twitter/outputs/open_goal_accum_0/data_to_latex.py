
# IMPORT
import pandas as pd
from typing import Dict, Tuple, Any, Optional
from my_utils import to_latex_with_note, format_p_value, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
# No shared mapping is required in this case as the tables labels are unique.

# TABLE 1:
df = pd.read_pickle('table_1.pkl')

# RENAME ROWS AND COLUMNS 
# Define labels to scientifically-suitable names
mapping: AbbrToNameDef = {
 'House': ('House of Representatives', 'Members of US Congress representing House'),
 'Senate': ('Senate', 'Members of US Congress representing Senate'),   
}

abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(
 df, 'table_1.tex',
 caption="Distribution of interactions among House of Representatives and Senate Members", 
 label='table:distribution_of_interactions',
 legend=legend)


# TABLE 2:
df = pd.read_pickle('table_2.pkl')

# FORMAT VALUES 
# Applying `format_p_value` to p-value column
df['p-value'] = df['p-value'].apply(format_p_value)

# RENAME ROWS AND COLUMNS 
# Define labels to scientifically-suitable names
mapping: AbbrToNameDef = {
 'Chi-square statistic': ('Chi-square statistic', 'Chi-square test statistic value indicating level of independence between variables'),
 'p-value': ('P-value', 'Statistical significance value of the Chi-square test statistic')
}

abbrs_to_names, legend = split_mapping(mapping)
df = df.rename(columns=abbrs_to_names, index=abbrs_to_names)

# Save as latex:
to_latex_with_note(
 df, 'table_2.tex',
 caption="Chi-square Test of Independence Result", 
 label='table:chi_square_result',
 legend=legend)

